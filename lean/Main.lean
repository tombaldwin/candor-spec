import CandorModel
/-- Emit the decision table as TSV: verb, argument, S, D, verdict. Consumed by
    `reference/differential_lean_vs_python.py`, which recomputes every row with
    `reference/policy_model.py` and fails on any disagreement. -/
def main : IO Unit := do
  for row in Candor.emitRows do
    IO.println row
