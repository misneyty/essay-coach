import os

from flask import Flask, jsonify, request, send_from_directory

from coach.session import (
    create_session,
    get_session,
    set_sections,
    set_stage,
    add_result,
)
from coach.parser import parse_essay
from coach.analyzers import (
    analyze_abstract,
    analyze_introduction,
    analyze_body_paragraph,
    analyze_conclusion,
    analyze_references,
)
from coach.assessor import assess
from coach.questions import generate

MAX_CHARS = 8000


def create_app():
    app = Flask(__name__, static_folder="static", static_url_path="")

    from anthropic import Anthropic

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        # Try loading from .env
        try:
            from dotenv import load_dotenv
            load_dotenv()
            api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        except ImportError:
            pass

    if not api_key:
        print("WARNING: ANTHROPIC_API_KEY not set. API calls will fail.")

    client = Anthropic(api_key=api_key)

    @app.route("/")
    def index():
        return send_from_directory("static", "index.html")

    # ── Session: create ─────────────────────────────────────────────

    @app.route("/api/session", methods=["POST"])
    def api_create_session():
        data = request.get_json(silent=True) or {}
        essay = data.get("essay", "").strip()

        if not essay:
            return jsonify({"error": "请粘贴论文内容。"}), 400
        if len(essay) > MAX_CHARS:
            return jsonify(
                {"error": f"论文字数超过上限（{MAX_CHARS}字），请分段提交。"}
            ), 400

        try:
            sections, structure_map, plagiarism_flag = parse_essay(client, essay)
        except Exception as e:
            return jsonify({"error": f"论文解析失败：{str(e)}"}), 500

        session_id = create_session(essay)
        set_sections(session_id, sections)
        set_stage(session_id, "structure_confirmed")

        return jsonify(
            {
                "session_id": session_id,
                "structure_map": structure_map,
                "sections": {
                    "title": sections.get("title", ""),
                    "abstract": sections.get("abstract", ""),
                    "introduction": sections.get("introduction", ""),
                    "body_count": len(sections.get("body", [])),
                    "conclusion": sections.get("conclusion", ""),
                    "references": sections.get("references", ""),
                },
                "plagiarism_flag": plagiarism_flag,
            }
        )

    # ── Session: confirm structure ──────────────────────────────────

    @app.route("/api/session/<session_id>/confirm", methods=["POST"])
    def api_confirm(session_id):
        s = get_session(session_id)
        if not s:
            return jsonify({"error": "会话已过期，请重新提交论文。"}), 404

        set_stage(session_id, "abstract")
        return jsonify({"status": "confirmed", "next_stage": "abstract"})

    # ── Session: analyze a stage ────────────────────────────────────

    @app.route(
        "/api/session/<session_id>/analyze/<stage>", methods=["POST"]
    )
    def api_analyze_stage(session_id, stage):
        s = get_session(session_id)
        if not s:
            return jsonify({"error": "会话已过期，请重新提交论文。"}), 404

        sections = s["sections"]
        if not sections:
            return jsonify({"error": "请先解析论文结构。"}), 400

        try:
            if stage == "abstract":
                result = analyze_abstract(client, sections.get("abstract", ""))
                next_stage = "introduction"
            elif stage == "introduction":
                result = analyze_introduction(
                    client, sections.get("introduction", "")
                )
                body = sections.get("body", [])
                next_stage = "body_0" if body else "conclusion"
            elif stage.startswith("body_"):
                idx = int(stage.split("_")[1])
                body = sections.get("body", [])
                if idx >= len(body):
                    return jsonify({"error": "段落索引超出范围。"}), 400
                result = analyze_body_paragraph(
                    client, body[idx], idx, len(body)
                )
                if idx + 1 < len(body):
                    next_stage = f"body_{idx + 1}"
                else:
                    next_stage = "conclusion"
            elif stage == "conclusion":
                result = analyze_conclusion(
                    client, sections.get("conclusion", "")
                )
                next_stage = "references"
            elif stage == "references":
                body_text = "\n\n".join(sections.get("body", []))
                result = analyze_references(
                    client, sections.get("references", ""), body_text
                )
                next_stage = "assessment"
            else:
                return jsonify({"error": f"未知的分析阶段：{stage}"}), 400

            add_result(session_id, stage, result)
            set_stage(session_id, next_stage)

            return jsonify({"stage": stage, "result": result, "next": next_stage})
        except Exception as e:
            return jsonify({"error": f"分析失败：{str(e)}"}), 500

    # ── Session: comprehensive assessment ───────────────────────────

    @app.route("/api/session/<session_id>/assess", methods=["POST"])
    def api_assess(session_id):
        s = get_session(session_id)
        if not s:
            return jsonify({"error": "会话已过期，请重新提交论文。"}), 404

        try:
            result = assess(client, s.get("results", {}))
            add_result(session_id, "assessment", result)
            set_stage(session_id, "questions_prompt")
            return jsonify({"stage": "assessment", "result": result})
        except Exception as e:
            return jsonify({"error": f"综合评估失败：{str(e)}"}), 500

    # ── Session: follow-up questions ────────────────────────────────

    @app.route("/api/session/<session_id>/questions", methods=["POST"])
    def api_questions(session_id):
        s = get_session(session_id)
        if not s:
            return jsonify({"error": "会话已过期，请重新提交论文。"}), 404

        data = request.get_json(silent=True) or {}
        if not data.get("include_questions", True):
            set_stage(session_id, "done")
            return jsonify({"stage": "questions", "result": None, "next": "done"})

        try:
            assessment = s.get("results", {}).get("assessment", "")
            result = generate(client, assessment, s.get("results", {}))
            add_result(session_id, "questions", result)
            set_stage(session_id, "done")
            return jsonify({"stage": "questions", "result": result, "next": "done"})
        except Exception as e:
            return jsonify({"error": f"生成问题失败：{str(e)}"}), 500

    # ── Session: modify / drill-down ────────────────────────────────

    @app.route("/api/session/<session_id>/modify", methods=["POST"])
    def api_modify(session_id):
        s = get_session(session_id)
        if not s:
            return jsonify({"error": "会话已过期，请重新提交论文。"}), 404

        data = request.get_json(silent=True) or {}
        section = data.get("section", "")
        point = data.get("point", "")

        if not section or not point:
            return jsonify({"error": "请指定要深入讨论的章节和要点。"}), 400

        sections = s["sections"]
        section_text = ""
        if section in ("abstract", "introduction", "conclusion", "references"):
            section_text = sections.get(section, "")
        elif section.startswith("body_"):
            idx = int(section.split("_")[1])
            body = sections.get("body", [])
            if idx < len(body):
                section_text = body[idx]

        from coach.prompts import modify_point_prompt

        try:
            prompts = modify_point_prompt(section, point, section_text)
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2048,
                temperature=0.4,
                system=prompts["system"],
                messages=[{"role": "user", "content": prompts["user"]}],
            )
            result = response.content[0].text
            return jsonify({"result": result})
        except Exception as e:
            return jsonify({"error": f"深入分析失败：{str(e)}"}), 500

    # ── Session: get state ──────────────────────────────────────────

    @app.route("/api/session/<session_id>", methods=["GET"])
    def api_get_session(session_id):
        s = get_session(session_id)
        if not s:
            return jsonify({"error": "会话已过期，请重新提交论文。"}), 404

        return jsonify(
            {
                "session_id": session_id,
                "current_stage": s["current_stage"],
                "results_keys": list(s["results"].keys()),
            }
        )

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="127.0.0.1", port=5000, debug=True)
