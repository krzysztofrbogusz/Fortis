"""Preview a candidate rule: what would this edit change, before you commit it.

Parses one rule from its definition string, splices it into a *copy* of the project's
rule set at a chosen time, re-derives the whole lexicon, and diffs the result against
the baseline. Every word whose surface moves is bucketed:

- **improved** — closer to its target (candidate distance < baseline),
- **regressed** — further from its target,
- **lateral** — changed but no closer or further,
- **ungraded** — surface moved but the word has no target to score against.

The net exact-match delta (over the graded words) is the headline. The project's own
rules are never mutated — the augmented inventory is built from fresh tuples — so the
baseline computed first stays valid.

Placement is load-bearing (it decides feeding/bleeding), so the report always states
where the rule was inserted; ``time=None`` means untimed, i.e. after every timed rule.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

from src.fortis.analysis.grading import compare
from src.fortis.application.deriving import derive_all
from src.fortis.application.rendering import render_syllabified
from src.fortis.application.tiers import lower_tiers
from src.fortis.loaders.rules import load_rule
from src.fortis.models.derivation import Derivation
from src.fortis.models.project import Project
from src.fortis.models.rules import RuleInventory
from src.fortis.result import Err, Ok, Result


@dataclass(frozen=True)
class WordChange:
    """One word whose surface moved under the candidate rule."""

    gloss: str
    ipa: str
    baseline: str
    candidate: str
    target: str | None
    baseline_distance: int | None
    candidate_distance: int | None

    @property
    def delta(self) -> int | None:
        """Change in target distance (negative = improved); ``None`` if ungraded."""
        if self.baseline_distance is None or self.candidate_distance is None:
            return None
        return self.candidate_distance - self.baseline_distance


@dataclass(frozen=True)
class WhatIf:
    """The full preview of a candidate rule against the lexicon."""

    definition: str
    time: int | None
    improved: tuple[WordChange, ...]
    regressed: tuple[WordChange, ...]
    lateral: tuple[WordChange, ...]
    ungraded: tuple[WordChange, ...]
    net_exact_delta: int  # graded words exact under candidate minus under baseline

    @property
    def touched(self) -> int:
        """How many words the candidate moved at all."""
        return len(self.improved) + len(self.regressed) + len(self.lateral) + len(self.ungraded)


def _surface(derivation: Derivation, project: Project) -> str:
    return render_syllabified(lower_tiers(derivation.surface), derivation.surface_boundaries, project)


def _augmented_rules(project: Project, candidate) -> RuleInventory:
    """A fresh rule inventory = the project's rules plus *candidate*, project's untouched."""
    augmented = RuleInventory({time: tuple(rules) for time, rules in project.rules.items()})
    for rule in candidate:
        augmented[rule.time] = (*augmented.get(rule.time, ()), rule)
    return augmented


def try_rule(project: Project, definition: str, time: int | None = None) -> Result[WhatIf, list[str]]:
    """Preview inserting the rule *definition* at *time*, diffing against the baseline.

    *definition* is Fortis rule notation (``target → result / context``, e.g.
    ``eː → ɛː / _ t``). Returns an ``Err`` list if it does not parse. The rule is given
    the id ``candidate``; a list ``definition`` (sub-rules) is spliced in order.
    """
    match load_rule("candidate", {"definition": definition, "time": time}, project.features):
        case Err(errs):
            return Err(errs)
        case Ok(candidate):
            pass

    swap = project.settings.grading.transposition_cost
    baseline = derive_all(project)
    candidate_run = derive_all(replace(project, rules=_augmented_rules(project, candidate)))

    improved: list[WordChange] = []
    regressed: list[WordChange] = []
    lateral: list[WordChange] = []
    ungraded: list[WordChange] = []
    base_exact = cand_exact = 0

    for base, cand in zip(baseline, candidate_run, strict=True):
        target = base.word.final
        base_surface, cand_surface = _surface(base, project), _surface(cand, project)
        if target is not None:
            base_dist = compare(base_surface, target, swap)
            cand_dist = compare(cand_surface, target, swap)
            base_exact += base_dist == 0
            cand_exact += cand_dist == 0
        else:
            base_dist = cand_dist = None
        if base_surface == cand_surface:
            continue
        change = WordChange(
            gloss=base.word.gloss, ipa=base.word.ipa,
            baseline=base_surface, candidate=cand_surface, target=target,
            baseline_distance=base_dist, candidate_distance=cand_dist,
        )
        if target is None:
            ungraded.append(change)
        elif change.delta < 0:
            improved.append(change)
        elif change.delta > 0:
            regressed.append(change)
        else:
            lateral.append(change)

    return Ok(
        WhatIf(
            definition=definition, time=time,
            improved=tuple(improved), regressed=tuple(regressed),
            lateral=tuple(lateral), ungraded=tuple(ungraded),
            net_exact_delta=cand_exact - base_exact,
        )
    )


def whatif_summary_line(whatif: WhatIf) -> str:
    """A one-line headline for stderr."""
    sign = "+" if whatif.net_exact_delta >= 0 else ""
    return (
        f"candidate touched {whatif.touched} word(s): "
        f"{len(whatif.improved)} improved, {len(whatif.regressed)} regressed "
        f"(net {sign}{whatif.net_exact_delta} exact) — see whatif.md"
    )


def _placement(time: int | None) -> str:
    return "untimed (after all timed rules)" if time is None else f"t={time} (after existing t={time} rules)"


def render_whatif(whatif: WhatIf, where: str) -> str:
    """The full ``whatif.md`` report."""
    sign = "+" if whatif.net_exact_delta >= 0 else ""
    lines = [
        f"# What-if — {where}",
        "",
        f"Candidate rule `{whatif.definition}` inserted at **{_placement(whatif.time)}**.",
        "",
        f"**Net {sign}{whatif.net_exact_delta} exact** over the graded lexicon — "
        f"{len(whatif.improved)} improved, {len(whatif.regressed)} regressed, "
        f"{len(whatif.lateral)} changed laterally, {len(whatif.ungraded)} ungraded moved.",
        "",
    ]
    if whatif.touched == 0:
        lines.append("The candidate changed no word's surface — it never fires, or its output matches.")
        return "\n".join(lines).rstrip() + "\n"
    lines += _change_table("Improved", whatif.improved)
    lines += _change_table("Regressed", whatif.regressed)
    lines += _change_table("Lateral (changed, no closer)", whatif.lateral)
    lines += _change_table("Ungraded (no target)", whatif.ungraded)
    return "\n".join(lines).rstrip() + "\n"


def _change_table(heading: str, changes: tuple[WordChange, ...]) -> list[str]:
    if not changes:
        return []
    graded = changes and changes[0].target is not None
    lines = [f"## {heading} ({len(changes)})", ""]
    if graded:
        lines += ["| word | baseline | candidate | target | dist |", "| --- | --- | --- | --- | ---: |"]
        for c in sorted(changes, key=lambda c: c.delta or 0):
            lines.append(
                f"| {c.gloss or c.ipa} | `{c.baseline}` | `{c.candidate}` | `{c.target}` "
                f"| {c.baseline_distance}→{c.candidate_distance} |"
            )
    else:
        lines += ["| word | baseline | candidate |", "| --- | --- | --- |"]
        for c in changes:
            lines.append(f"| {c.gloss or c.ipa} | `{c.baseline}` | `{c.candidate}` |")
    lines.append("")
    return lines
