# Exam Timetable Algorithm Comparison

A small, self-contained Python prototype that builds a synthetic multi-branch exam dataset, compares Genetic Algorithm (GA), Evolution Strategy (ES), and Evolutionary Programming (EP), and exports the best timetable found.

## Run

```powershell
python main.py
```

Optional examples:

```powershell
python main.py --students 1800 --sessions 12 --population 80 --generations 150 --seed 7
python main.py --branch-sizes CS=600,AM=240,AD=240,CB=240,IS=240,CI=240
python main.py --start-date 2026-11-06 --end-date 2026-11-13 --population 80 --generations 150
```

Outputs are written to `output/`: `timetable.csv`, `algorithm_comparison.csv`, and `run_summary.json`.

## Dashboard

```powershell
python app.py
```

Open `http://127.0.0.1:8766`. The page displays semester/date/session tables, fitness and session-load charts, explains the method, and can rerun the comparison using editable settings and an exam date range. Weekends are skipped and each weekday provides two sessions. Stop the server with Ctrl+C.

## Synthetic data assumptions

- Default population: 1,800 students total (600 Core CSE and 240 in each of five other branches). This resolves the earlier conflicting totals by using the 1,800-total interpretation; adjust `--branch-sizes` to experiment.
- Branch abbreviations: `CS` Core CSE, `AM` AI & ML, `AD` AI & Data Science, `CB` CS & Business Systems, `IS` Information Science, `CI` CS & IoT.
- USNs are synthetic, e.g. `1BM23CS001`. They are not real student records.
- Each branch has a common curriculum for semesters III–VIII based on the prior draft; cross-listed course titles are merged into shared courses. Students take all subjects for their branch and semester.
- Rooms 201–220 and 401–420 each seat 60. Room assignment is computed from the session's course enrollments, allowing one course to use several halls.
- The example uses 12 exam sessions. This is configurable and is a prototype assumption, not a college calendar.
- A hard student conflict is prevented by assigning each semester's exams to distinct sessions. This makes feasibility reliable and lets the algorithms focus on reducing back-to-back papers. Same-session cross-semester course conflicts are separately penalized and repaired by the evaluator.

## Algorithms

All methods share the same candidate encoding (one session index per exam), fitness function, initialization, runtime budget, and deterministic seed for fair comparison. They use a common greedy feasibility repair for student conflicts. GA uses tournament selection and two-parent uniform crossover; ES uses a `(mu + lambda)` mutation-and-survivor strategy; EP uses parent/offspring mutation followed by pairwise tournament selection. Because ES and EP have many variants, these are explicitly described as educational variants, not the only canonical definitions.

The score is hard student clashes × 1,000,000 + hall overflow × 1,000,000 + student back-to-back exam pairs × 100 + session load imbalance. The dashboard picks the best result by feasibility first, then back-to-back count, then load balance; runtime is reported but is not part of fitness.
