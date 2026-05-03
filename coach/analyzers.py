from .prompts import (
    analyze_abstract_prompt,
    analyze_introduction_prompt,
    analyze_body_prompt,
    analyze_conclusion_prompt,
    analyze_references_prompt,
)


def _call_claude(client, prompts):
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        temperature=0.4,
        system=prompts["system"],
        messages=[{"role": "user", "content": prompts["user"]}],
    )
    return response.content[0].text


def analyze_abstract(client, abstract_text):
    return _call_claude(client, analyze_abstract_prompt(abstract_text))


def analyze_introduction(client, intro_text):
    return _call_claude(client, analyze_introduction_prompt(intro_text))


def analyze_body_paragraph(client, para_text, para_index, total_count):
    return _call_claude(
        client, analyze_body_prompt(para_text, para_index, total_count)
    )


def analyze_conclusion(client, conclusion_text):
    return _call_claude(client, analyze_conclusion_prompt(conclusion_text))


def analyze_references(client, references_text, body_text):
    return _call_claude(
        client, analyze_references_prompt(references_text, body_text)
    )
