from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List, Literal, Optional

from synapdrive_ai.bci.intent_generator import generate_intent
from synapdrive_ai.pipeline import SynapDrivePipeline


FallbackPolicy = Literal["freeze", "abort", "complete"]


@dataclass
class TaskStep:
    intent_text: str
    min_confidence: float = 0.55
    fallback: FallbackPolicy = "freeze"
    image_label: Optional[str] = None
    label: Optional[str] = None

    def __post_init__(self) -> None:
        if self.label is None:
            self.label = self.intent_text


@dataclass
class TaskPlan:
    name: str
    steps: List[TaskStep]

    def __len__(self) -> int:
        return len(self.steps)


@dataclass
class StepTrace:
    step_index: int
    label: str
    intent_text: str
    pipeline_status: str
    pipeline_confidence: float
    min_confidence: float
    fallback_applied: Optional[FallbackPolicy]
    block_reason: Optional[str]
    evaluation_score: float
    elapsed_s: float


@dataclass
class PlanTrace:
    plan_name: str
    outcome: str
    n_steps: int
    n_completed: int
    n_deferred: int
    n_aborted: int
    steps: List[StepTrace]
    total_elapsed_s: float
    created_utc: float = field(default_factory=time.time)

    def summary(self) -> str:
        lines = [
            f"Plan: {self.plan_name}  →  {self.outcome.upper()}",
            f"  Steps: {self.n_steps}  completed: {self.n_completed}  deferred: {self.n_deferred}  aborted: {self.n_aborted}",
            f"  Total time: {self.total_elapsed_s:.3f}s",
        ]
        for s in self.steps:
            tag = {
                "success": "✓",
                "blocked": "✗",
                "deferred": "⏸",
                "aborted": "⊘",
            }.get(s.pipeline_status, "?")
            lines.append(
                f"    [{tag}] step {s.step_index}: {s.label!r}  conf={s.pipeline_confidence:.2f}  score={s.evaluation_score:.2f}"
                + (f"  → {s.block_reason}" if s.block_reason else "")
            )
        return "\n".join(lines)


class ExecutorBridge:
    def __init__(
        self,
        simulate_delay: bool = False,
        pipeline: Optional[SynapDrivePipeline] = None,
    ) -> None:
        self._pipe = pipeline or SynapDrivePipeline(simulate_delay=simulate_delay)

    def execute(self, plan: TaskPlan) -> PlanTrace:
        step_traces: List[StepTrace] = []
        plan_start = time.time()
        overall_outcome = "completed"
        n_completed = n_deferred = n_aborted = 0

        for idx, step in enumerate(plan.steps):
            step_start = time.time()
            trace = self._execute_step(idx, step)
            trace.elapsed_s = round(time.time() - step_start, 4)
            step_traces.append(trace)

            if trace.pipeline_status == "success":
                n_completed += 1
            elif trace.pipeline_status == "deferred":
                n_deferred += 1
                if overall_outcome == "completed":
                    overall_outcome = "frozen"
            elif trace.pipeline_status == "aborted":
                n_aborted += 1
                overall_outcome = "aborted"
                break
            else:
                if step.fallback == "abort":
                    n_aborted += 1
                    overall_outcome = "aborted"
                    break
                n_deferred += 1
                if overall_outcome == "completed":
                    overall_outcome = "frozen"

        if overall_outcome == "completed" and (n_deferred > 0 or n_aborted > 0):
            overall_outcome = "partial"

        return PlanTrace(
            plan_name=plan.name,
            outcome=overall_outcome,
            n_steps=len(plan.steps),
            n_completed=n_completed,
            n_deferred=n_deferred,
            n_aborted=n_aborted,
            steps=step_traces,
            total_elapsed_s=round(time.time() - plan_start, 4),
        )

    def _execute_step(self, idx: int, step: TaskStep) -> StepTrace:
        base_packet = generate_intent(step.intent_text)
        out = self._pipe.run_intent_packet(base_packet, image_label=step.image_label)

        intent_out = out.get("intent", {}) or {}
        eval_out = out.get("evaluation", {}) or {}
        pipeline_status = out.get("status", "blocked")
        confidence = float(intent_out.get("confidence", 0.0))
        block_reason = out.get("reason")
        eval_score = float(eval_out.get("score", 0.0))
        fallback_applied: Optional[FallbackPolicy] = None

        if pipeline_status == "success" and confidence < step.min_confidence:
            fallback_applied = step.fallback
            if step.fallback == "freeze":
                pipeline_status = "deferred"
                block_reason = (
                    f"Step confidence {confidence:.2f} < required {step.min_confidence:.2f} → freeze"
                )
            elif step.fallback == "abort":
                pipeline_status = "aborted"
                block_reason = (
                    f"Step confidence {confidence:.2f} < required {step.min_confidence:.2f} → abort"
                )

        return StepTrace(
            step_index=idx,
            label=step.label or step.intent_text,
            intent_text=step.intent_text,
            pipeline_status=pipeline_status,
            pipeline_confidence=round(confidence, 4),
            min_confidence=step.min_confidence,
            fallback_applied=fallback_applied,
            block_reason=block_reason,
            evaluation_score=eval_score,
            elapsed_s=0.0,
        )
