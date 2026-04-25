from pathlib import Path

import yaml

PROMPTS_DIR = Path(__file__).resolve().parents[1] / "prompts"


class PromptBuilder:
    def build(self, prompt_version: str, exercise) -> tuple[str, str]:
        template_path = PROMPTS_DIR / f"{prompt_version}.yaml"
        payload: dict = {}
        if template_path.exists():
            payload = yaml.safe_load(template_path.read_text(encoding="utf-8")) or {}

        # Build format kwargs from exercise model
        format_kwargs = {
            "exercise_id": exercise.id,
            "title": exercise.title,
            "concept": exercise.concept,
            "llm_context": exercise.llm_context,
            "common_mistakes": ", ".join(exercise.common_mistakes) if exercise.common_mistakes else "Not specified",
        }

        system_template = payload.get(
            "system",
            "You are an educational tutor. Never provide full solutions or complete final code.",
        )
        user_template = payload.get(
            "template",
            (
                "Exercise {exercise_id}: {title}\n"
                "Concept: {concept}\n"
                "Context: {llm_context}\n"
                "Give a level-appropriate hint only."
            ),
        )

        # Format both prompts with exercise data
        system_prompt = system_template.format(**format_kwargs)
        user_prompt = user_template.format(**format_kwargs)
        
        return system_prompt, user_prompt
