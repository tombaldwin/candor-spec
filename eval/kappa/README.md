# RQ3 inter-rater-agreement (κ) study — reproducible artifact

Regenerated 2026-07-21 (the original per-find labels were not retained). Reconstructs the coded
dataset from `../../SOUNDNESS.md §8.1` + `../../SOUNDNESS-LOG.md` under an explicit inclusion rule
(window 2026-06-18 → 2026-07-16; distinct-mechanism-per-finding, bundled rows disaggregated to their
recorded count; the 2026-07-18 dispatch cohort excluded), then re-codes it under the published
three-axis protocol with three coders and computes Cohen's κ.

- `findings_full.json` — 65 findings, author-reconstructed labels (rater 1) + mechanism/evidence.
- `findings_blind.json` — same 65, labels stripped (coder input).
- `coding_rater2.json`, `coding_adjudicator.json` — two blind LLM re-codings (adjudicator under the
  sharpened silent-vs-precision rule).
- `kappa_perfind.csv` — the per-find three-coder label table (the confusion-matrix source).
- `compute_kappa.py` — Cohen's κ per axis × rater-pair, raw agreement, confusion, asymptotic +
  bootstrap (seed 20260721) 95% CIs. `python3 compute_kappa.py`.

CAVEAT: all three coders are LLM instances applying the written rubric, so κ measures **protocol
reproducibility**, not human inter-annotator independence (κ is correspondingly high). N=62 is the
clean 3-way intersection (rater 2 re-unitized 3 finds). A human replication is the open camera-ready item.
