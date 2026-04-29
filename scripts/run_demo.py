from __future__ import annotations

from app.agents.chat import run_assessment_chat, run_final_notice_chat
from app.agents.voice import run_resolution_voice
from app.eval.scenarios import demo_borrower, seeded_scenarios


def main() -> None:
    borrower = demo_borrower()
    scenario = seeded_scenarios()[-1]
    assessment = run_assessment_chat(borrower, scenario, "v2")
    resolution = run_resolution_voice(borrower, scenario, assessment.handoff_summary, "v2")
    final_notice = run_final_notice_chat(borrower, scenario, resolution.handoff_summary, "v2")
    for result in [assessment, resolution, final_notice]:
        print(f"\n## {result.stage.value} ({result.channel.value}) -> {result.outcome}")
        print("token_counts:", result.token_counts)
        for message in result.messages:
            print(f"{message.role}: {message.content}")


if __name__ == "__main__":
    main()
