# Fortis User Guide

Fortis is a featural, autosegmental phonology engine. You define your phonological system using TOML files in the `inventories/` directory, and Fortis loads them to validate, syllabify, and transform phonological representations.

---

## Inventory files

Fortis reads six TOML files from the `inventories/` directory:

| File                        | Purpose                              |
| --------------------------- | ------------------------------------ |
| `features.toml`             | The phonological feature system      |
| `rules.toml`                | Sound change rules                   |
| `syllable_constraints.toml` | Syllable structure constraints       |
| `words.toml`                | Lexicon of words with glosses        |
| `sonorities.toml`           | Sonority hierarchy levels            |
| `diacritics.toml`           | Diacritics and their feature effects |

Each file is described in detail below.

---

## Features (`inventories/features.toml`)

The features file defines the phonological features available in your system. Each feature is an entry where the key is the feature name and the value is an inline table specifying its properties.

### Required fields

| Field  | Type   | Description                                                       |
| ------ | ------ | ----------------------------------------------------------------- |
| `tier` | string | Which tier this feature belongs to. One of: `segment`, `syllable` |
| `type` | string | The feature type. One of: `unary`, `binary`, `scalar`             |

### Optional fields

| Field      | Type           | Description                                                            |
| ---------- | -------------- | ---------------------------------------------------------------------- |
| `short`    | string         | Abbreviation for the feature. Defaults to the feature name if omitted. |
| `values`   | table          | For `scalar` features only — maps integer keys to label strings.       |
| `children` | string or list | Child feature names. A single string or a list of strings.             |

### Feature types

- **unary** — a feature that is either present or absent (e.g. `[nasal]`). No `values` field needed; values are automatically `{1: "present"}`.
- **binary** — a feature with a plus/minus opposition (e.g. `[±sonorant]`). No `values` field needed; values are automatically `{0: "absent", 1: "present"}`.
- **scalar** — a feature with multiple graded values (e.g. `[length]` with `1 = short, 2 = long`). Requires the `values` field.

### Examples

A binary feature:

```toml
consonantal = { tier = "segment", type = "binary", short = "cons" }
```

A unary feature with an abbreviation:

```toml
nasal = { tier = "segment", type = "unary", short = "nas" }
```

A unary feature with children (using a list):

```toml
manner = { tier = "segment", type = "unary", children = ["continuant", "sonorant", "strident"] }
```

A unary feature with a single child (using a string):

```toml
click = { tier = "segment", type = "unary", children = "lateral" }
```

A scalar feature with values:

```toml
length = { tier = "segment", type = "scalar", short = "ln", values = { 1 = "short", 2 = "long", 3 = "overlong" } }
```

A scalar feature with negative values:

```toml
glottal_aperture = { tier = "segment", type = "scalar", short = "glap", values = { -1 = "constricted", 0 = "neutral", 1 = "spread" } }
```

### Validation rules

- Feature names are case-insensitive and will be normalized to lowercase.
- `short` abbreviations are normalized to lowercase and stripped of surrounding whitespace.
- `children` entries are normalized to lowercase and stripped of whitespace.
- `values` labels are normalized to lowercase and stripped of surrounding whitespace.
- `values` keys must be integers (negative values are allowed).
- A scalar feature **must** include `values`. Omitting it will produce an error.
- A `short` field, if provided, must be a non-empty string. If omitted, the feature name is used as the abbreviation.
- Every feature must specify both `tier` and `type`. Empty strings are not accepted.

---

## Rules (`inventories/rules.toml`)

Sound change rules define transformations applied to phonological representations. Each rule is an entry keyed by a numeric ID, with a name, description, and definition string.

### Fields

| Field         | Type   | Description                                     |
| ------------- | ------ | ----------------------------------------------- |
| `name`        | string | Human-readable rule name                        |
| `description` | string | What the rule does                              |
| `definition`  | string | The rule written in Fortis notation (see below) |

### Rule notation

The general form of a rule is:

```
A → B / C_D // E_F
```

- **A** — target: what elements are matched
- **B** — result: what they become
- **C_D** — context: the environment (before `_` = left context, after `_` = right context)
- **E_F** — exception: an environment where the rule does **not** apply

The context (`/ C_D`) is required. The exception clause (`// E_F`) is optional and may only appear when a context is present.

### Symbols

| Symbol        | Meaning                                 |
| ------------- | --------------------------------------- |
| `p`           | Letter shorthand                        |
| `[+syll]`     | Feature bundle: syllabic is present     |
| `[-syll]`     | Feature bundle: syllabic is absent      |
| `[syll: 1]`   | Feature bundle: syllabic has value 1    |
| `[2 height]`  | Feature bundle: height has value 2      |
| `[hgt: high]` | Feature bundle: height has label "high" |
| `[]`          | Wildcard — any segment                  |
| `#`           | Word boundary                           |
| `$`           | Syllable boundary                       |
| `∅`           | Null segment (insertion/deletion)       |

### Quantifiers

Quantifiers specify how many times an element may match:

| Notation       | Meaning   |
| -------------- | --------- |
| `[+cons]{3}`   | Exactly 3 |
| `[+cons]{0,3}` | 0 to 3    |
| `[+cons]{2,}`  | 2 or more |
| `[+cons]{,3}`  | Up to 3   |
| `[+cons]?`     | 0 or 1    |
| `[+cons]*`     | 0 or more |
| `[+cons]+`     | 1 or more |

### Control elements

| Notation             | Meaning                                               |
| -------------------- | ----------------------------------------------------- |
| `!p`, `![+syll]`     | Negation — not this letter or element                 |
| `([+syll][+cons])`   | Grouping — matched as a unit                          |
| `([h: 3] \| [h: 2])` | Disjunction — match any branch                        |
| `[α high]`           | Alpha variable — bind or match a feature value        |
| `[!α high]`          | Alpha variable — match any value except the bound one |
| `[<1: +high>]`       | Conditional feature — apply only if condition holds   |
| `V=[+syll]`          | Save a reference to a matched element                 |
| `@V`                 | Recall a previously saved reference                   |

### Contour notation

For scalar features with contour values (e.g. tone):

| Notation           | Meaning                                     |
| ------------------ | ------------------------------------------- |
| `[cont: 1>2>3]`    | Contour with values 1, 2, 3 in sequence     |
| `[cont: @initial]` | Match at the start of the contour           |
| `[cont: @final]`   | Match at the end of the contour             |
| `[cont: @2]`       | Match at the second position of the contour |
| `[cont: @all]`     | Match at every position of the contour      |

### Example

```toml
[1200.final_devoicing]
name = "Final devoicing"
description = "Devoices the final consonant in a sequence"
definition = "[+cons, -syll] → [-vc] / _#"
```

---

## Syllable constraints (`inventories/syllable_constraints.toml`)

Defines which syllable structures are permitted. Each entry is keyed by a numeric ID and specifies onset constraints.

### Fields

| Field             | Type   | Description                                          |
| ----------------- | ------ | ---------------------------------------------------- |
| `onset`           | table  | Constraints on syllable onsets                       |
| `onset.required`  | string | Feature bundle that must be present in the onset     |
| `onset.forbidden` | string | Feature bundle that must not be present in the onset |

### Example

```toml
[1200]
onset = { required = "[+cons, -syll]*", forbidden = "$[+cons, +nas, +vel]" }
```

This requires at least one consonant in the onset and forbids nasal+velar sequences.

---

## Words (`inventories/words.toml`)

The lexicon. Each entry maps a word written in IPA (with stress and syllable markers) to a gloss.

### Fields

| Field   | Type   | Description                |
| ------- | ------ | -------------------------- |
| `gloss` | string | English gloss for the word |

### Notation in word entries

- `ˈ` — primary stress (placed before the stressed syllable)
- `.` — syllable boundary
- `ː` / `ːː` — long / overlong vowel markers
- Diacritics are written directly after the segment they modify

### Example

```toml
"ˈxen.ti" = { gloss = "in front" }
"mexˈteːr" = { gloss = "mother" }
"ˈɣʷe.roː" = { gloss = "eagle" }
"ˈbʱleɣʷ.moː" = { gloss = "flower" }
```

---

## Sonorities (`inventories/sonorities.toml`)

Defines the sonority hierarchy used for syllabification. Each entry is a sonority class keyed by name.

### Fields

| Field         | Type    | Description                                        |
| ------------- | ------- | -------------------------------------------------- |
| `level`       | integer | Sonority level (higher = more sonorous)            |
| `feature_set` | string  | Feature bundle describing this class               |
| `nucleus`     | boolean | Whether this class can serve as a syllable nucleus |

### Example

```toml
vowel = { level = 5, feature_set = "syllabic: +", nucleus = true }
glide = { level = 4, feature_set = "syllabic: -, consonantal: +", nucleus = false }
nasal = { level = 3, feature_set = "consonantal: +, nasal: +", nucleus = false }
sibilant = { level = 2, feature_set = "consonantal: +, strident: +", nucleus = false }
plosive = { level = 1, feature_set = "consonantal: +", nucleus = false }
```

---

## Diacritics (`inventories/diacritics.toml`)

Maps Unicode diacritic characters to their phonological effects. Each entry is keyed by the diacritic character.

### Fields

| Field         | Type    | Description                                                                  |
| ------------- | ------- | ---------------------------------------------------------------------------- |
| `tier`        | string  | Which tier this diacritic affects: `segment` or `syllable`                   |
| `type`        | string  | Positioning: `before`, `after`, or `combining`                               |
| `feature_set` | string  | Feature bundle this diacritic applies                                        |
| `boundary`    | boolean | Whether this diacritic marks a syllable boundary (optional, default false)   |
| `default`     | boolean | Whether this diacritic is a default representation (optional, default false) |

### Diacritic types

- **before** — placed before the segment it modifies (e.g. stress marker `ˈ`)
- **after** — placed after the segment it modifies (e.g. aspiration `ʰ`, length `ː`)
- **combining** — combined with the preceding character (e.g. nasalization `̃`)

### Example

```toml
# Segmental diacritics
"ʰ" = { tier = "segment", type = "after", feature_set = "-vc, 1 glap, 0 tns" }
"ʷ" = { tier = "segment", type = "after", feature_set = "+labial, +rounded" }

# Length markers
"ː" = { tier = "segment", type = "after", feature_set = "length: long" }
"ːː" = { tier = "segment", type = "after", feature_set = "length: overlong" }

# Stress
"ˈ" = { tier = "syllable", type = "before", boundary = true, feature_set = "stress: primary", default = true }
"."  = { tier = "syllable", type = "after", boundary = true, feature_set = "", default = true }

# Tone letters
"˥" = { tier = "syllable", type = "after", feature_set = "tone: 5", default = true }
```
