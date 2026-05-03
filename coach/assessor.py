from .prompts import assess_overall_prompt


def assess(client, all_results):
    summary = _format_results_summary(all_results)
    prompts = assess_overall_prompt(summary)
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        temperature=0.4,
        system=prompts["system"],
        messages=[{"role": "user", "content": prompts["user"]}],
    )
    return response.content[0].text


def _format_results_summary(results):
    parts = []
    for stage, text in results.items():
        parts.append(f"=== {stage.upper()} ===\n{text}\n")
    return "\n".join(parts)
