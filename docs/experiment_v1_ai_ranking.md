# Experiment notes: baseline versus AI ranking

The current experiment runner supersedes this earlier single-variant template. Use `docs/evaluation_protocol.md` and `run_experiments.py` for the controlled A/B/C/D design.

The research question remains whether an AI ranking layer can select a more contextually suitable recipe from candidates retrieved by the frozen baseline without replacing the baseline retrieval process.

A changed selection is not automatically a better selection. Evaluate ingredient utilisation, hard constraint satisfaction, time compliance, missing requested ingredients, human relevance, and usefulness. Report failures as well as successes. Do not fabricate latency, API usage, outcome measurements, or human ratings. Actual run outputs are written to timestamped files under `outputs/`.
