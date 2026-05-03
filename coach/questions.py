from .prompts import generate_questions_prompt


def generate(client, assessment_text, all_results):
    blind_spots = _extract_blind_spots(all_results)
    prompts = generate_questions_prompt(assessment_text, blind_spots)
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        temperature=0.5,
        system=prompts["system"],
        messages=[{"role": "user", "content": prompts["user"]}],
    )
    return response.content[0].text


def _extract_blind_spots(results):
    spots = []
    for stage, text in results.items():
        for line in text.split("\n"):
            if "⚠️" in line or "missing" in line.lower() or "缺少" in line:
                spots.append(f"[{stage}] {line.strip()}")
                if len(spots) >= 6:
                    break
        if len(spots) >= 6:
            break
    return "\n".join(spots) if spots else "No specific blind spots identified."
