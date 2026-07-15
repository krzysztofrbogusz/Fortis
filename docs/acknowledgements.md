# Acknowledgements and data sources

This lists only material Fortis **redistributes** whose licence requires attribution. Sources that
were merely consulted — reference books, papers, Wikipedia — are not copyrightable knowledge and
are cited *for reference where they are used* (a `rules.toml` comment, a `words.toml` note, a
project `SOURCE.md`), not here.

The engine ships no built-in phonology; the engine code is original. Per-project provenance lives
beside the data ([`latin_to_french/SOURCE.md`](../projects/latin_to_french/SOURCE.md),
[`pie_to_english/SOURCE.md`](../projects/pie_to_english/SOURCE.md),
[`halle_vaux_wolfe/SOURCE.md`](../projects/halle_vaux_wolfe/SOURCE.md),
[`spe/SOURCE.md`](../projects/spe/SOURCE.md)).

## Latin → French — DiaSim / DiaCLEF2025 / FLLAPS (GPL-3.0)

[DiaSim](https://github.com/clmarr/DiaSim) (branch `gamma`; Marr & Mortensen). The
`latin_to_french` `rules.toml` is a hand re-authoring of the DiaCLEF2025 cascade in Fortis
notation, and the lexicon's per-stage targets come from **FLLAPS / FLLexPlus2024**. Both are
GPL-3.0; the upstream source is not bundled — fetch it from the repository above.

## Word frequencies — hermitdave/FrequencyWords (MIT)

[hermitdave/FrequencyWords](https://github.com/hermitdave/FrequencyWords) (`2018/{fr,en}_50k`;
OpenSubtitles counts via [OPUS](https://opus.nlpl.eu/)). Used for the `frequency` column of each
project's lexicon (token-weighted accuracy).

## PIE → English lexicon — Wiktionary (CC BY-SA 4.0)

[Wiktionary](https://www.wiktionary.org/) contributors, via the [kaikki.org](https://kaikki.org/)
extracts ([wiktextract](https://github.com/tatuylonen/wiktextract), MIT tool; Wiktionary data).
`projects/pie_to_english/words.toml` is derived from it and carries the **share-alike** CC BY-SA
4.0 — so must any redistribution. The project's `rules.toml` and `tools/` are original work under
the repo's own licence.

## Licensing

Fortis (engine + original docs) is **PolyForm Noncommercial 1.0.0** ([`LICENSE`](../LICENSE)).

| Material | Licence |
| --- | --- |
| Fortis engine + docs | PolyForm Noncommercial 1.0.0 |
| Latin→French `rules.toml` + lexicon (from DiaSim / FLLAPS) | GPL-3.0 |
| PIE→English `words.toml` (from Wiktionary) | CC BY-SA 4.0 (share-alike) |
| PIE→English `rules.toml` + `tools/` (original) | PolyForm Noncommercial 1.0.0 |
| French / English frequency lists | MIT |

Descriptive, not a legal instrument — consult each upstream project's own licence.
