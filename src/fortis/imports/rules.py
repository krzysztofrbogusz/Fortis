"""Rule dataclass — the parsed representation of a phonological rule.

A rule is the output of the *parse* stage and the input to the *match* and
*apply* stages.  By the time a Rule object exists, parsing and validation
are already done; application code can assume the rule is well-formed.
"""

from dataclasses import dataclass, field

from src.fortis.models.application_type import ApplicationType
from src.fortis.models.element import Element


@dataclass
class RuleDefinition:
    """A phonological rule parsed from SPE notation.

    The general form is  A → B / C_D // E_F  where:

    - **target** (A): what elements are matched
    - **result** (B): what they become
    - **left_context** (C): environment before the target
    - **right_context** (D): environment after the target
    - **exception_left** (E): exception environment before the target
    - **exception_right** (F): exception environment after the target

    None means "unconstrained" (no condition on that side).

    Args:
        rule_id: Unique identifier from the TOML key (e.g. "final_devoicing").
        name: Human-readable name (e.g. "Final devoicing").
        description: Optional longer description.
        time: Application time (lower = applied earlier).
        target: List of Elements that must match.
        result: List of Elements describing the transformation.
        left_context: Left-side context, or None for no constraint.
        right_context: Right-side context, or None for no constraint.
        exception_left: Left-side exception context, or None.
        exception_right: Right-side exception context, or None.
    """

    rule_id: str
    name: str
    time: int = 0
    description: str = ""
    target: list[Element] = field(default_factory=list)
    result: list[Element] = field(default_factory=list)
    left_context: list[Element] | None = None
    right_context: list[Element] | None = None
    exception_left: list[Element] | None = None
    exception_right: list[Element] | None = None
    application: ApplicationType = ApplicationType.simultaneous
