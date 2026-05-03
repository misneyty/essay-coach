import json
import re
from .prompts import parse_structure_prompt


def parse_essay(client, essay_text):
    prompts = parse_structure_prompt(essay_text)
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        temperature=0.3,
        system=prompts["system"],
        messages=[{"role": "user", "content": prompts["user"]}],
    )
    raw = response.content[0].text

    # Strip markdown code fences if present
    raw = re.sub(r"^```(?:json)?\s*\n?", "", raw.strip())
    raw = re.sub(r"\n?```\s*$", "", raw)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # Retry with a stronger prompt suffix
        retry_response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            temperature=0.1,
            system=prompts["system"],
            messages=[
                {"role": "user", "content": prompts["user"]},
                {
                    "role": "assistant",
                    "content": raw,
                },
                {
                    "role": "user",
                    "content": "The JSON above is invalid. Please output ONLY valid JSON this time, with no additional text.",
                },
            ],
        )
        raw2 = retry_response.content[0].text
        raw2 = re.sub(r"^```(?:json)?\s*\n?", "", raw2.strip())
        raw2 = re.sub(r"\n?```\s*$", "", raw2)
        data = json.loads(raw2)

    structure_map = data.get(
        "structure_map", _build_structure_map(data)
    )
    plagiarism_flag = data.get("plagiarism_flag", "")

    sections = {
        "title": data.get("title", ""),
        "abstract": data.get("abstract", ""),
        "introduction": data.get("introduction", ""),
        "body": data.get("body", []),
        "conclusion": data.get("conclusion", ""),
        "references": data.get("references", ""),
    }

    return sections, structure_map, plagiarism_flag


def _build_structure_map(data):
    lines = []
    idx = 1
    if data.get("title"):
        lines.append(f"Section {idx}: Title ({_wc(data['title'])} words)")
        idx += 1
    if data.get("abstract"):
        lines.append(f"Section {idx}: Abstract ({_wc(data['abstract'])} words)")
        idx += 1
    if data.get("introduction"):
        lines.append(
            f"Section {idx}: Introduction ({_wc(data['introduction'])} words)"
        )
        idx += 1
    for i, para in enumerate(data.get("body", [])):
        lines.append(
            f"Section {idx}: Body Paragraph {i + 1} ({_wc(para)} words)"
        )
        idx += 1
    if data.get("conclusion"):
        lines.append(
            f"Section {idx}: Conclusion ({_wc(data['conclusion'])} words)"
        )
        idx += 1
    if data.get("references"):
        lines.append(
            f"Section {idx}: References ({_wc(data['references'])} words)"
        )
        idx += 1
    return "\n".join(lines)


def _wc(text):
    return len(text.split())
