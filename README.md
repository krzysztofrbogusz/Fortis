# Fortis

A diachronic phonology engine. Everything is user-supplied in `inventories/`
(feature system, letters, diacritics, sonority scale, syllable parameters,
lexicon, sound-change rules); the engine segments each word into feature
bundles, runs it through the rules in chronological order, and prints a
step-by-step derivation with syllable structure. The reference data models the
development from Proto-Indo-European to Proto-Germanic.

Run the derivations:

```
python -m src.fortis.main
```

## Layout

A strict downward dependency DAG — each layer imports only from those above it
(`models` ← `parsing` ← `loaders` ← `application`); `models` is inert data.

```
fortis/
├── inventories/                 # user-authored data
│   ├── features.toml  letters.csv  diacritics.toml
│   ├── sonorities.toml  syllable_parts.toml
│   └── words.toml  rules.toml
├── docs/                        # user_guide, notation reference, feature/rule docs
├── tests/
└── src/fortis/
    ├── config.py                # paths, value symbols, greek alphabet, special symbols
    ├── result.py                # Result / Ok / Err
    ├── main.py                  # load → segment → derive → print the trace
    │
    ├── general/                 # generic helpers, zero domain knowledge
    │   ├── file_handling.py     #   load_toml_file, load_csv_file
    │   ├── presenting.py        #   symbol presentation helpers
    │   └── utils.py             #   safe_int, ...
    │
    ├── models/                  # INERT DATA — imports only stdlib + within models
    │   ├── values.py            #   Value, AlphaRef, AlphaOp, ContourEdge, contours
    │   ├── tiers.py             #   Tier
    │   ├── specs.py             #   FeatureSpec, PatternSpec, ResultSpec
    │   ├── bundles.py           #   FeatureBundle, PatternBundle, ResultBundle
    │   ├── bindings.py          #   Bindings (alpha + element-ref state)
    │   ├── elements.py          #   Element union (LetterRef, Group, Quantified, $, …)
    │   ├── rules.py             #   ApplicationMode, StructuralDescription, Rule, RuleInventory
    │   ├── features.py          #   FeatureKind, Feature, FeatureInventory
    │   ├── inventories.py       #   Letter/Diacritic/Sonority/SyllablePart/Word + inventories
    │   ├── project.py           #   Project (every inventory bundled together)
    │   ├── derivation.py        #   DerivationStep, Derivation
    │   └── syllable.py          #   Syllable (index-based onset/nucleus/coda)
    │
    ├── parsing/                 # STRING → models       (depends on: models)
    │   ├── lexer.py             #   tokenise rule notation
    │   ├── bundles.py           #   parse_value, parse_*_spec, parse_*_bundle
    │   ├── notation.py          #   parse_definition / parse_sequence → Elements
    │   └── rule_validation.py   #   structural validation of a parsed rule
    │
    ├── loaders/                 # FILE → models         (depends on: models, parsing)
    │   ├── features.py          #   features.toml      → FeatureInventory
    │   ├── letters.py           #   letters.csv        → LetterInventory
    │   ├── diacritics.py  sonorities.py  syllable_parts.py  words.py
    │   ├── rules.py             #   rules.toml (bodies parsed via parsing.notation)
    │   └── project.py           #   load everything    → Project
    │
    └── application/             # THE ENGINE            (depends on: models, parsing, loaders)
        ├── combining.py         #   bundle algebra: combine, merge (node-delink), compare
        ├── matching.py          #   pattern_matches; find_matches (sequence matcher); full_match
        ├── applying.py          #   apply_match: rewrite a matched locus
        ├── syllabifying.py      #   syllabify: sonority + onset/coda-pattern boundaries
        ├── segmentation.py      #   string_to_sequence: IPA → feature bundles
        ├── rendering.py         #   sequence_to_string, render_syllabified, describe_change
        └── deriving.py          #   apply_rule per mode; derive a word → Derivation
```
