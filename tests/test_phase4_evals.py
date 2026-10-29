"""Phase 4 Tests: Verify 25-question evaluation benchmark, tool selection accuracy, and fact verification."""

from __future__ import annotations

import json

import pytest

from evals.run_evals import QUESTIONS_PATH, RESULTS_MD_PATH, run_evaluation_suite


@pytest.mark.asyncio
async def test_eval_suite_25_questions_and_markdown_report(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify /evals contains 25 questions, scores tool selection & answer correctness, and writes evals/results.md."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    questions = json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))
    assert len(questions) == 25

    summary = await run_evaluation_suite()
    assert summary["total"] == 25
    assert summary["tool_correct"] == 25
    assert summary["tool_accuracy_pct"] == 100.0
    assert summary["answer_correct"] == 25
    assert summary["answer_accuracy_pct"] == 100.0
    assert RESULTS_MD_PATH.exists()

    md_text = RESULTS_MD_PATH.read_text(encoding="utf-8")
    assert "Tool Selection Accuracy:" in md_text
    assert "| Q01 |" in md_text
    assert "| Q25 |" in md_text
