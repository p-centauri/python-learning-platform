from pathlib import Path
from .contracts import HumanReview, Metrics, Observation, Policy, Suite, Variant, Verdict


async def observe(
    suite: Suite, directory: Path, variant: Variant = "task-gated-v1"
) -> tuple[Observation, ...]:
    """Execute each versioned controlled case in its own empty owned workspace."""
    raise NotImplementedError


def measure(suite: Suite, observations: tuple[Observation, ...]) -> Metrics:
    """Validate full coverage; calculate exact explicit denominators and boundary facts."""
    raise NotImplementedError


def decide(
    suite: Suite,
    observations: tuple[Observation, ...],
    policy: Policy = Policy(),
    reviews: tuple[HumanReview, ...] = (),
) -> Verdict:
    """Apply versioned finite thresholds with manual review separately pinned to the candidate."""
    raise NotImplementedError
