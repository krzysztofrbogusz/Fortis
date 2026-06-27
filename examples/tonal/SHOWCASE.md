# Showcase — autosegmental phonology in Fortis

Tone in Fortis lives on its own **tier**: a tone is an *autosegment* joined to a vowel by an
**association line**, not a value sealed inside the vowel's feature bundle. That single design
choice makes a whole family of tonal phenomena fall out — three of them genuinely **impossible**
to express in a "flat" model where every feature lives inside its segment, the rest natural here
and awkward everywhere else.

Each example is a real derivation in the tiny tonal language in this directory. Run it and read
the trace. High tone is a combining acute (`a` + `◌́`); a floating high is written `⟨◌́⟩`.

```
python -m src.fortis.main --inventories examples/tonal
```

---

## Impossible in a flat model

### 1 · Tonal stability — a tone outlives its vowel

```
katá   "tonal stability"
    100: Final vowel loss
        ka.ta˦ → ka˦t        (ata˦ → a˦t)
    Surface: ka˦t
```

The word-final vowel is deleted — but its high tone does **not** vanish. It re-anchors onto the
preceding syllable: `ka` → `ka˦`.

**Why a flat model can't.** If the tone is a feature *inside* the vowel, deleting the vowel
deletes the tone with it — full stop. Here the tone is a separate object on the tier; removing
its anchor leaves it *floating*, and stability re-docks it onto the neighbour. The tone is never
destroyed because it was never part of the segment.

### 2 · Floating grammatical tone — a tone with no segment of its own

```
naka⟨◌́⟩   "floating-tone docking"
    50: Floating-tone docking
        na.ka → na.ka˦
    Surface: na˦k          (final-vowel loss then applies)
```

`⟨◌́⟩` is a floating high **suffix** — a tonal morpheme that is purely a tone, with no vowel.
It docks onto the stem (here, leftward, onto the syllable it follows).

**Why a flat model can't.** A feature with no host segment is not representable at all — there
is nothing for it to be a feature *of*. On the tier it is simply an autosegment that has not
associated yet, carrying a lexical *position* so it knows which way to dock.

---

## Natural here, awkward in a flat model

### 3 · High-tone spread — one tone, many syllables

```
táka   "high-tone spread"
    0: High-tone spread
        ta˦.ka → ta˦.ka˦
    Surface: ta˦k          (final-vowel loss then applies)
```

One high tone associates to **both** syllables — a *single* autosegment with two association
lines, not two copies.

**Why this matters.** A flat model could copy the tone value onto each vowel and get the same
surface — but then they are two independent tones. Delink one, or merge them under the OCP, and
the others do not follow. Here they are genuinely *one object*, so they behave as one: this is
the difference between spreading a tone and duplicating it.

### 4 · Tone displacement — a tone shifts off its sponsor

```
python -m src.fortis.main --inventories examples/tonal --rules examples/tonal/rules_shift.toml
```
```
táka   (the same word, a different language)
    0: High-tone shift (displacement)
        ta˦.ka → ta.ka˦      (a˦ → a, a → a˦)
    Surface: ta.ka˦
```

The high tone delinks from its own vowel and re-anchors one syllable to the right — the **same**
autosegment, moved (note the trace: `a˦ → a` on the first vowel, `a → a˦` on the second).

**Why this matters.** The tone surfaces on a vowel that never lexically "had" it. In a flat
model this is a featural sleight of hand — clear a feature here, set it there, with no object
that moved. On the tier it is one association line erased and another drawn; the autosegment
itself is untouched. Spread (§3) and shift here are the *same* operation differing by one delink
— which is exactly the generalization a flat model misses.

---

## The showstopper — a contour tone from two level tones

```
ka̋tā   "contour formation"        (◌̋ = extra-high, ◌̄ = mid)
    100: Final vowel loss
        ka˥.ta˧ → kât              (a˥ta˧ → ât)
    Surface: kât
```

Two **level** tones: extra-high on the first syllable, mid on the second. The second vowel is
deleted — and *its* mid tone, by stability, crowds onto the first syllable, which already carries
extra-high. The result is **two tones on one vowel**: a falling contour, `â`.

**Why a flat model can't.** This is the founding argument for autosegmental phonology (Goldsmith
1976). A flat model can *store* a contour as one complex value, but it cannot **derive** one this
way: the derivation needs two tones to exist independently of their vowels (so one survives its
vowel's deletion) and then to associate to the *same* tone-bearing unit. Both steps are possible
only because tone is an object on its own tier. A contour, here, is literally what you see — two
autosegments sharing one anchor.

*(Limb order follows tier order, which is creation/lexical order — correct for lexical melodies
and crowding like this; the engine doesn't yet reconstruct order after operations that reshuffle
a tier.)*

---

The same tier representation also enforces the **OCP** (adjacent identical tones merge into one
multiply-linked autosegment). The notation is in `docs/change_notation_rules.md` §1.8–§1.9 (tier
references and lexical floating tones) and §2.12 (the spread / dock / delink operations); the
engine internals are in the project `README.md` under *Autosegmental tiers*.
