from __future__ import annotations

from app.core.store import REPORTS_DIR, write_json
from app.eval.learning_loop import evaluate_prompt_version


def run_meta_evaluation() -> dict[str, str]:
    flawed_baseline = evaluate_prompt_version("baseline_v1", "eval_v1_flawed")
    flawed_aggressive = evaluate_prompt_version("aggressive_candidate", "eval_v1_flawed")
    fixed_aggressive = evaluate_prompt_version("aggressive_candidate", "eval_v2_compliance_gated")

    caught = flawed_aggressive.mean_score > 0.6 and fixed_aggressive.compliance_pass_rate < 1.0
    payload = {
        "meta_eval_case": "flawed evaluator over-weighted collections outcome and under-weighted compliance",
        "flawed_baseline_mean": flawed_baseline.mean_score,
        "flawed_aggressive_mean": flawed_aggressive.mean_score,
        "fixed_aggressive_mean": fixed_aggressive.mean_score,
        "fixed_aggressive_compliance_pass_rate": fixed_aggressive.compliance_pass_rate,
        "caught": caught,
        "correction": (
            "Evaluator v2 adds a hard compliance gate and increases compliance weight from 0.15 to 0.30. "
            "Any policy violation now forces total score to 0 for that stage."
        ),
    }
    json_path = write_json(REPORTS_DIR / "meta_evaluation_case.json", payload)
    md_path = REPORTS_DIR / "meta_evaluation.md"
    md_path.write_text(
        "\n".join(
            [
                "# Meta-Evaluation Case",
                "",
                "The primary evaluator v1 was intentionally flawed: it rewarded task success heavily and allowed compliance failures to retain a deceptively acceptable aggregate score.",
                "",
                f"Flawed baseline mean: `{flawed_baseline.mean_score}`",
                f"Flawed aggressive mean: `{flawed_aggressive.mean_score}`",
                f"Fixed aggressive mean: `{fixed_aggressive.mean_score}`",
                f"Fixed aggressive compliance pass rate: `{fixed_aggressive.compliance_pass_rate}`",
                "",
                "Correction: evaluator v2 applies a hard compliance gate. If an agent violates policy, that stage score becomes 0 regardless of apparent collection success.",
                "",
                f"Caught flaw: `{caught}`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return {"json": str(json_path), "report": str(md_path)}
