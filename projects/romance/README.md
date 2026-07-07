# romance — reconstruction testbed

Not a normal Fortis derivation project (no rules cascade yet). This holds
`cognates.toml`: Romance-language cognate sets, in broad IPA, as **seed data for the
reconstruction experiment** described in [`../../docs/reconstruction_sketch.md`](../../docs/reconstruction_sketch.md).

The goal is the *inverse* of what Fortis normally does — recover the common ancestor and
the sound-change rules from the daughter forms alone. Romance is the chosen testbed
because the ancestor (Vulgar/Classical Latin) is **attested**, making this a known-answer
benchmark: reconstruct from the daughters, then score against the `lat` column.

`lat` is the answer key, **not** an input — hold it out when running any reconstruction.
Daughters: `srd` (Sardinian, the conservative outlier), `ita`, `spa`, `por`, `fra`, `ron`.
A daughter is omitted from a set where the word was borrowed/replaced rather than inherited.

IPA is approximate and should be verified before serious use.
