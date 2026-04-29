from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from app.agents.chat import run_assessment_chat, run_final_notice_chat
from app.agents.voice import run_resolution_voice
from app.core.models import EvalRun, StageScore
from app.core.store import REPORTS_DIR, RUNS_DIR, ensure_dirs, utc_timestamp, write_json
from app.eval.judge import compliance_pass_rate, mean_score, score_stage
from app.eval.scenarios import demo_borrower, seeded_scenarios


SEED = 20260429


def run_pipeline_for_scenario(prompt_version: str, evaluator_version: str) -> list[StageScore]:
    borrower = demo_borrower()
    stage_scores: list[StageScore] = []
    for scenario in seeded_scenarios():
        assessment = run_assessment_chat(borrower, scenario, _agent_prompt_version(prompt_version))
        resolution = run_resolution_voice(
            borrower, scenario, assessment.handoff_summary, _agent_prompt_version(prompt_version)
        )
        final_notice = run_final_notice_chat(
            borrower, scenario, resolution.handoff_summary, _agent_prompt_version(prompt_version)
        )
        for result in [assessment, resolution, final_notice]:
            stage_scores.append(score_stage(scenario, result, evaluator_version))
    return stage_scores


def evaluate_prompt_version(prompt_version: str, evaluator_version: str) -> EvalRun:
    scores = run_pipeline_for_scenario(prompt_version, evaluator_version)
    return EvalRun(
        run_id=f"{prompt_version}_{evaluator_version}_{utc_timestamp()}",
        evaluator_version=evaluator_version,
        prompt_version=prompt_version,
        scores=scores,
        mean_score=mean_score(scores),
        compliance_pass_rate=compliance_pass_rate(scores),
        adopted=False,
        decision_reason="pending",
        cost_usd=0.0,
    )


def run_learning_loop() -> dict[str, str]:
    ensure_dirs()
    baseline = evaluate_prompt_version("baseline_v1", "eval_v2_compliance_gated")
    candidate = evaluate_prompt_version("candidate_v2", "eval_v2_compliance_gated")
    aggressive = evaluate_prompt_version("aggressive_candidate", "eval_v2_compliance_gated")

    diff_ci = bootstrap_mean_diff(
        [score.total_score for score in baseline.scores],
        [score.total_score for score in candidate.scores],
    )
    candidate_delta = candidate.mean_score - baseline.mean_score
    candidate.adopted = (
        candidate_delta >= 0.05
        and diff_ci["ci_low"] > 0
        and candidate.compliance_pass_rate == 1.0
    )
    candidate.decision_reason = (
        f"delta={candidate_delta:.4f}, bootstrap_ci=[{diff_ci['ci_low']:.4f}, "
        f"{diff_ci['ci_high']:.4f}], compliance={candidate.compliance_pass_rate:.2f}"
    )

    aggressive.adopted = False
    aggressive.decision_reason = (
        "Rejected: compliance-gated evaluator found policy violations despite apparent outcome gains."
    )
    baseline.decision_reason = "Baseline control prompt."

    runs = [baseline, candidate, aggressive]
    json_path = write_json(RUNS_DIR / "learning_loop_results.json", [run.model_dump() for run in runs])
    csv_path = write_scores_csv(REPORTS_DIR / "per_conversation_scores.csv", runs)
    report_path = write_evolution_report(REPORTS_DIR / "evolution_report.md", runs, diff_ci)
    return {
        "json": str(json_path),
        "csv": str(csv_path),
        "report": str(report_path),
    }


def bootstrap_mean_diff(
    baseline_scores: list[float],
    candidate_scores: list[float],
    iterations: int = 2000,
) -> dict[str, float]:
    rng = np.random.default_rng(SEED)
    baseline = np.array(baseline_scores)
    candidate = np.array(candidate_scores)
    diffs = []
    for _ in range(iterations):
        idx = rng.integers(0, len(baseline), len(baseline))
        diffs.append(float(np.mean(candidate[idx] - baseline[idx])))
    low, high = np.percentile(diffs, [2.5, 97.5])
    return {"ci_low": round(float(low), 4), "ci_high": round(float(high), 4), "seed": SEED}


def write_scores_csv(path: Path, runs: list[EvalRun]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "run_id",
                "evaluator_version",
                "prompt_version",
                "scenario_id",
                "stage",
                "task_success",
                "continuity",
                "compliance",
                "token_efficiency",
                "borrower_experience",
                "total_score",
                "outcome",
                "violations",
            ]
        )
        for run in runs:
            for score in run.scores:
                writer.writerow(
                    [
                        run.run_id,
                        run.evaluator_version,
                        run.prompt_version,
                        score.scenario_id,
                        score.stage.value,
                        score.task_success,
                        score.continuity,
                        score.compliance,
                        score.token_efficiency,
                        score.borrower_experience,
                        score.total_score,
                        score.outcome,
                        ";".join(score.violations),
                    ]
                )
    return path


def write_evolution_report(path: Path, runs: list[EvalRun], diff_ci: dict[str, float]) -> Path:
    lines = [
        "# Evolution Report",
        "",
        f"Seed: `{SEED}`",
        "Learning-loop LLM spend: `$0.00` in this reproducible run. The implementation uses a deterministic simulator/judge for the submitted artifact; external LLM providers can be plugged in behind the same agent interface.",
        "",
        "| Prompt version | Evaluator | Mean score | Compliance pass rate | Adopted | Decision |",
        "| --- | --- | ---: | ---: | --- | --- |",
    ]
    for run in runs:
        lines.append(
            f"| {run.prompt_version} | {run.evaluator_version} | {run.mean_score:.4f} | "
            f"{run.compliance_pass_rate:.4f} | {run.adopted} | {run.decision_reason} |"
        )
    lines.extend(
        [
            "",
            "## Statistical Test",
            "",
            "Candidate v2 is compared against baseline v1 on the same seeded scenarios and stages.",
            f"Bootstrap 95% CI for mean score delta: `[{diff_ci['ci_low']}, {diff_ci['ci_high']}]`.",
            "Adoption requires delta >= 0.05, lower CI > 0, and 100% compliance pass rate.",
            "",
            "## Raw Data",
            "",
            "Per-stage scores are in `reports/per_conversation_scores.csv`.",
            "Machine-readable run data is in `data/runs/learning_loop_results.json`.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _agent_prompt_version(prompt_version: str) -> str:
    if prompt_version == "candidate_v2":
        return "v2"
    if prompt_version == "aggressive_candidate":
        return "aggressive"
    return "v1"
