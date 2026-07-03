# Latin → French: roadmap to full-lexicon accuracy (and 200 words)

Status when written: **106/140 exact** (~99 rule-derived + 7 documented lexical
marks). This doc analyzes how to reach *all* words passing, how to grow the
lexicon to 200, and settles the semivowel/diphthong representation question.
The repair history and bug taxonomy live in `latin_to_french_review.md`.

## 1. What the remaining misses are — and are not

Measured facts about the 34 current misses:

- **Not a transcription-convention problem.** Folding every non-contrastive
  glide distinction (`w`/`u̯`, `j`/`i̯`, offglide diacritics, residual length)
  converts exactly **1** miss into a pass (*nouer* `n̪u̯e` ~ `n̪we`). The other
  33 differ in real segmental content.
- **Not missing rule blocks.** The port now has 690 rules against ~703
  rule-lines in the source — near parity. This session's wins split between
  genuinely missing single rules (`ow→u` s547-548, `yj→ɥi` s514-517) and
  mistranslated/mis-ordered ones (geminate `ll`, labiovelar `ɥ`). The residue
  is of the same kind: **per-rule translation faults, invisible until a word's
  derivation traverses them.**
- **Not lexical.** The 7 genuinely lexical splits (ail/maille, pâtre, fosse,
  or, six, cerf, graal) are already word-scoped with documented rationale.
  Everything left is rule-governed diphthong/glide development.

Conclusion: the path to 140/140 is a **systematic audit of rule translations**,
not more per-word trace-chasing (which finds the same faults, one expensive
word at a time) and not more lexical marks (which would fake it).

## 2. Measure the ceiling first: run DiaSim as the oracle

Before promising 140/140 via rule fixes, measure what **the source cascade
itself** scores on these words. DiaSim is runnable Java
(github.com/clmarr/DiaSim, branch `gamma`; java 8 is on this machine, DiaSim
may want a newer JDK). Derive our 140 (later 200) Latin inputs through
DiaCLEF2025 in DiaSim itself and diff three ways:

| comparison | meaning |
|---|---|
| DiaSim ✓, Fortis ✗ | **port bug — guaranteed fixable.** The audit's work-list. |
| DiaSim ✗, Fortis ✗ | source limitation: needs original scholarship, a gold-standard correction, or (rarely) a lexical mark. |
| DiaSim ✗, Fortis ✓ | we out-derive the source (already true for some repaired words); fine, but flag in case the gold entry is wrong. |

This converts "get everything passing" from an open-ended goal into a bounded
one: **match-or-beat the oracle on every word, and account explicitly for every
word the oracle itself misses.** The honest ceiling for pure rule-derivation is
the oracle's score plus whatever source bugs we can fix that its author hasn't.

## 3. The rule-audit table (the user-proposed NL translation pass — endorsed)

Translate each source rule into natural language, then verify the Fortis
translation against both. Concretely: one table (CSV or MD in the project dir,
`rule_audit.csv`), one row per source rule-line:

```
source_line | source_formula | NL_description | port_rule_id(s) | status | note
```

with `status` ∈ {`verified`, `suspect`, `missing`, `dropped-deliberately`}.

Why this works — the evidence from this session: every real win came from
reading the source region directly (source-diff), and the NL step is what
catches the two dominant fault classes, because both are *silent* in a formula-
to-formula transliteration:

1. **Feature-space mismatches** (DiaSim `[+front,-syl]` means a glide; Fortis's
   coronals are `+front` too). Saying the rule in English — "a yod is absorbed
   after…" — forces the species question.
2. **Convention mismatches** (bare vowel = unstressed; `{a;b}` alternations;
   stress riding on literals).

Staging, worst-first (regions already implicated by the misses):
- **Later Old French, source 2357–2790** (the oi/ui/eau/l-vocalization block)
  — every remaining diphthong miss traverses it.
- **Middle French, 3011–3301** (nasalization tails, final-consonant effacement).
- Then the earlier periods, which the 106 passing words have largely validated.

~700 rows is mechanical but large; at an honest ~1 min/rule of real checking
this is a few sessions of work. The audit is also **exactly the work the
oracle diff (§2) prioritizes** — audit first the rules that the DiaSim-✓/
Fortis-✗ words traverse. Do §2 first; it turns the audit from exhaustive to
targeted.

## 4. Verify the targets themselves (gold-standard audit)

At least one attested entry is dubious: *sanglier* is given as `/sɑ̃ɡlie/` but
standard reference pronunciation is `/sɑ̃ɡlije/`. The attested column was
hand-carried; it should be **re-derived mechanically from FLLexPlus2024**
(DiaSim's own gold standard, same repo) with an explicit, documented
normalization:

- strip syllable dots; `ɡ`(U+0261)→`g`; keep dentals (the lexicon is dental);
- **fold non-contrastive glide species** — `u̯`→`w`, `i̯`→`j` in prevocalic
  position (French has no contrast; see §5);
- keep nasal vowels, ə, and length as FLLex has them.

The normalization function should live in the scorer AND be stated in
`SOURCE.md`, so "passing" is well-defined. This immediately converts *nouer*
and any other convention-only misses, and catches wrong golds like *sanglier*
before we burn time "fixing" the cascade toward a wrong target.

## 5. Representation: semivowels, glides, diphthongs

**Recommendation: keep diphthongs as two-segment sequences; do NOT make them
contour segments. Adopt the convention: semivowel (-cons) = tautosyllabic
offglide of a falling diphthong; glide (+cons) = onset (prevocalic) position.**

Why two segments, not contours:

- **The diachrony is *about* the halves.** Pope's rules independently address
  each half constantly: stress shift `ie̯ → je`, lowering `j → ɛ̯`, offglide
  absorption, the syllabicity swap `yj → ɥi`, nasalization of one half only.
  As a contour segment (`aperture: 1->0` etc., like the affricates'
  `continuant: ->+`), every one of these becomes feature surgery with no way
  to refer to "the second element" positionally — the entire source rule
  format stops mapping onto ours.
- Contours are the right tool where **no rule needs half-access and the
  transition is unanalyzable**: affricates, tone contours. Diphthongs in a
  diachronic cascade are the opposite case.
- The engine expresses both fine; this is purely convention, and the criterion
  is: *choose the representation the source's rule set can be translated into
  line-by-line*. That is two segments.

Why the -cons/+cons species split (rather than one yod):

- It is already load-bearing: glide-formation outputs `+cons`; DiaSim's own
  line 27 (`{j;w} > [+cons,-son] / __ [+syl]`) makes prevocalic yods
  consonantal. The port's residual faults are *violations* of the convention
  (nouer's late hiatus rule emits `u̯` prevocalically where the convention
  demands `w`), not faults *of* it.
- French itself: falling diphthongs die out during the cascade; everything
  that survives to Modern French is onset-glide + vowel. So the invariant
  "semivowel exists only inside a falling diphthong" self-destructs by 1400 —
  a good sanity check: **any semivowel in final output is a cascade bug.**

Enforcement, three cheap pieces:
1. State the convention in `default_system.md` (letters exist for both species;
   the *rules* maintain the invariant).
2. Sweep the port for rules that emit a semivowel in prevocalic position or a
   glide as an offglide; fix each (this is a bounded grep, not an audit).
3. Late-cascade guard rule mirroring source line 27 (prevocalic semivowel →
   glide) as a normalization backstop, plus the scorer fold of §4.

(When syllabification lands — see the planned onset/coda constraint work — the
species could in principle be *derived* from syllable position and collapsed to
one letter. Revisit then; don't block on it.)

## 6. Growing the lexicon to 200

Pull ~60 more entries from FLLexPlus2024 (same repo), **stratified, not
random**: pick words that exercise the under-validated cascade regions — oi/ui
diphthongs, nasal tails, -eau/-al vocalization, geminates, learned doublets —
plus some easy CV(C) words as ballast. Expect the score to *drop* on ingest
(new words walk unvalidated paths); that is the point — they are the
regression suite for the §3 audit. Import the gold column mechanically per §4.

## 7. Recommended sequence

1. **Gold re-derivation + scorer normalization** (§4) — hours; immediately
   reclassifies convention-only misses and bad golds. (nouer, sanglier, …)
2. **Convention sweep + backstop rule** (§5) — small, bounded.
3. **DiaSim oracle run** on all words (§2) — gives the fixable work-list and
   the honest ceiling.
4. **Targeted rule audit** (§3) over the rules traversed by DiaSim-✓/Fortis-✗
   words, worst regions first; fix with the standing gate (regenerate →
   byte-identity → tests → score → zero-regression → commit).
5. **Expand to 200** (§6), then loop 3–4 on the new misses.
6. Whatever remains after the oracle is matched: per-word scholarship, gold
   corrections, or documented lexical marks — each explicitly justified, never
   a silent hardcode.

---

## 8. Execution log (oracle built + first fixes) — 113/140

**Oracle is operational.** DiaSim (github.com/clmarr/DiaSim @gamma) compiled with
`brew install openjdk` (javac 26) and run non-interactively:
```
javac -d bin src/*.java          # in the cloned DiaSim dir
java -cp bin DiachronicSimulator -files_only -rules DiaCLEF2025 \
     -lex FLLexPlus2024.txt -out oracle -diacrit
```
Outputs `oracle/derivation/etym*.txt` (per-word `#latin# >>> *#pred# (GOLD:#g#)`
+ full rule-numbered trace) and `oracle/resultEditDistances.csv`. **DiaSim's own
accuracy on all 1512 FLLex words: 82.0% exact, 92.9% within-1, 97.8% within-2.**
Join scripts + `trace.py <gloss>` (side-by-side DiaSim vs Fortis trace) live in
the job tmp dir.

**Oracle partition of our 140 words** (at session start, Fortis 106): 99 both ✓,
**24 DiaSim-✓/Fortis-✗ = guaranteed-fixable port bugs**, 7 Fortis-beats-DiaSim,
10 both-✗ (source ceiling; we already match DiaSim exactly on avers/moelle/tien/
sanglier). **DiaSim's ceiling on this sample is 123/140.** Gold column verified:
0 discrepancies vs FLLex (the hand-carried attested was already correct).

**Fixes landed this session (106 → 113, all oracle-guided, all gated zero-regression):**
- `ũj̃/ỹj̃ → wĩ/ɥĩ` nasal glide-swap (source 2648, was missing) + word-initial
  yod→ɟ hardening (source 1128, was missing) → **coin, juin, pointure**.
- intertonic e→i raising given a `stress: none` guard (source's bare e = unstressed)
  → **vermeil** (tonic e no longer wrongly raised before -cul- ʎ).
- yod-absorption companion matching the **contour affricate** (Fortis affricates
  are `continuant: ->+`, so the `[-continuant]` rule missed them; source 382) → **laize**.
- e̯-deletion companion for the +cons-j-before-consonant, +rounded-nucleus case
  (source 2174; the original rule's `-consonantal` context missed Fortis's +cons j)
  → **cuir**.
- scorer folds non-contrastive **u̯→w, i̯→j** (French has no glide/semivowel
  contrast; symmetric on engine+gold) → **nouer**.

**Recurring bug class confirmed** (the dominant one): DiaSim rule *contexts* use
`[-cons]` for glides and `[-cont]` for affricate onsets; Fortis's glides are
`[+cons]` and affricates carry a `->+` contour, so faithfully-translated contexts
silently fail to match. Fix per-rule by matching the segment by *place/manner*
(front, high, strident, rounded) instead of by consonantality/continuancy.

**Remaining port bugs (deeper, diagnosed):** joue (offglide-transparent
lenition — broadening regresses blanche, needs care), chartre (palatal→t̪ before
C must precede affrication), able (posttonic syncope + β→b/_l), saunier (intertonic
syncope feeding l-vocalization), chou/coups (final-l vocalization timing / tonic-o),
eau/ive/Aisne/pucelle/pinceau (deep early -kw-/-k- palatalization divergences),
rouille (β-deletion + i-not-j deletion, source 3292), première (aria-yod metathesis),
vieux (tonic-vowel + -tl- path), époux (prosthetic-é retention). Each has its
DiaSim trace as the spec.

---

## 9. Lexicon expanded to 195; scorer convention adopted — 159/195

**Expanded 140 → 195 words** (Task 5). Pulled 55 more entries from FLLexPlus2024,
selected via the oracle to be DiaSim-derivable and spread across phonological
shapes (script + `expand.json` in the job tmp dir). Mechanical gold import from
FLLex; each new row added to `correctness.md` and `words.toml`. **40 of the 55
passed immediately** (Fortis already handles them); the 15 misses are all
DiaSim-✓ port bugs (new work-list).

**Scorer convention (Task 2/4):** `gen_correctness.py`/`score.py` now fold the
non-contrastive **u̯→w, i̯→j** (French has no glide/semivowel contrast), applied
symmetrically to engine output and gold. This is the principled tool for a
non-contrast (vs forcing the engine to emit one arbitrary member); it converts
*nouer* and is documented here + should be echoed in `SOURCE.md`.

**Score:** original 140 now **114/140** (from 106), new 55 **45/55**, **total
159/195 (81.0%)** — matching DiaSim's own 82% ballpark. All gated: default/pie
byte-identical, 632 engine tests green, zero regressions per fix.

**Additional fixes this segment (oracle-guided):**
- **prosthesis stress** — the prosthetic vowel before word-initial sC now carries
  secondary stress (DiaSim keeps it ˌe, protecting it from the e→ə→∅ reduction)
  → **étaim, époux** (écuyer partially).
- **yod-rule reordering** — j-after-i deletion moved *before* ʎ→j (matching
  DiaSim rule 471 < 743), so the /ij/ ending survives (**fille /fij/**) while the
  early diphthong yod still deletes (lit, six). **outil /uti/** is a lexical
  silent-l exception (DiaSim also derives *utij and misses it) — word-scoped.

**Convention note (semivowel/glide):** the global flip (make offglides -cons like
DiaSim) is NOT viable — the port's 690 hand-authored rules are written for
Fortis's +cons glides, and flipping collapsed the score to 7/140. The right
approach is per-rule: match glides/affricates by place/manner in rule *contexts*
(done for laize, cuir), and fold the non-contrast in scoring (done). joue's
offglide-transparent lenition remains the one case needing careful per-rule work
(broadening the intervocalic voicing regressed blanche).

**Remaining new-word port bugs (diagnosed, deeper):** doigt (final-t̪ retention),
janvier/jeudi/ton (spurious labial glide), chamois (a-nasalization), lai (a→ɛ
before the compound aiʲ yod — the simple rule misfired on lacs), loche (ʒ/ʃ
voicing), moyenne (ed→wa), poêle (sil→l vs z), rumeur (or→œ), sautier, chartre,
and the earlier deep set. Each has its DiaSim trace as spec.
