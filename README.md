# Essay Coach 论文写作教练

An AI-powered academic writing coach that provides multi-dimensional feedback on essays — structure, logic, language, and references. Built with Claude API and Flask.

AI 驱动的论文学术写作教练，从结构、逻辑、语言到引用的多维度诊断，引导学生自主优化而非代写。

## Features 功能

- **Structure Parsing 结构解析**: Automatically identifies Title, Abstract, Introduction, Body paragraphs, Conclusion, and References
- **Abstract Check 摘要检查**: Background, purpose, methods, results, conclusion completeness
- **Introduction Review 引言审查**: Focus progression, research question clarity, literature context, logical fallacies
- **Body Paragraph Analysis 段落分析**: Topic sentences, evidence relevance, logic gaps, transitions, language quality with radar scores
- **Conclusion Evaluation 结论评估**: Summary quality, limitations, future directions, new-evidence detection
- **Reference Audit 参考文献校对**: APA 7 format, in-text citation matching, source diversity
- **Comprehensive Assessment 综合评估**: Top strength, 3 priority fixes, actionable next step
- **Follow-up Questions 追问引导**: Open-ended thinking questions targeting argument blind spots
- **Interactive Workflow 交互式流程**: Stage-by-stage analysis with continue/modify options

## Quick Start 快速开始

### Prerequisites

- Python 3.10+
- [Anthropic API key](https://console.anthropic.com/)

### Setup

```bash
# Clone the repo
git clone git@github.com:misneyty/essay-coach.git
cd essay-coach

# Install dependencies
pip install -r requirements.txt

# Set your API key
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Run the app
python app.py
```

Then open **http://localhost:5000** in your browser.

### Usage 使用

1. Paste your essay (max 8000 characters) into the text area
2. Review the auto-generated structure map and confirm
3. Step through each analysis stage — click "Continue" to proceed or "Modify" to dive deeper
4. View the comprehensive assessment and optional follow-up questions

## Tech Stack 技术栈

| Layer | Technology |
|-------|-----------|
| Backend | Python 3 + Flask |
| AI / LLM | Anthropic Claude API (Sonnet 4) |
| Frontend | Vanilla HTML + CSS + JavaScript |
| Session | In-memory (server-side, 30-min TTL) |

## Project Structure 项目结构

```
essay-coach/
├── app.py                  # Flask entry point + API routes
├── requirements.txt        # Python dependencies
├── .env.example            # API key template
├── claude.md               # Claude Code slash command definition
├── coach/
│   ├── __init__.py
│   ├── session.py          # In-memory session management
│   ├── parser.py           # Essay structure parsing
│   ├── prompts.py          # Claude system/user prompt templates
│   ├── analyzers.py        # Stage A–E analysis functions
│   ├── assessor.py         # Comprehensive synthesis
│   └── questions.py        # Follow-up question generation
└── static/
    ├── index.html          # Single-page web UI
    ├── style.css           # Styles
    └── app.js              # Client-side state & API logic
```

## Privacy & Academic Integrity 隐私与学术诚信

- Essays are held **in-memory only** and expire after 30 minutes of inactivity — nothing is persisted to disk
- The tool **refuses full-paragraph rewrites** — it provides directional suggestions only
- Potential plagiarism is flagged with a reminder to cite properly

## License

MIT
