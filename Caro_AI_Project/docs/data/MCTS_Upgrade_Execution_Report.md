# MCTS upgrade execution report

This report tracks execution of `MCTS_Upgrade_Execution_Prompt.md`. A later
phase is authorized only when the preceding gate is marked `passed` with
evidence.

## Status summary

| Phase | Status | Next phase authorized |
|---|---|---|
| Phase 0 — baseline | passed | yes |
| Phase 1 — tactical gate and progressive widening | passed | yes |
| Phase 2 — rollout and performance | passed | yes |
| Phase 3 — strength qualification | in_progress | no |
| Phase 4 — pilot data and hard-label safeguards | not_started | no |
| Phase 5 — soft targets and full dataset v2 | not_started | no |

## Phase 0 — Freeze and reproduce baseline

**Status:** `passed`

### Repository inspection

- No `AGENTS.md` file was found under the project.
- Pre-existing untracked files were preserved:
  `docs/Phan_cong_thanh_vien.md`, the recheck report, the upgrade plan, and the
  execution prompt.
- No implementation file was changed during Phase 0.

### Commands

Initial sandboxed test attempt:

```powershell
.\myenv\Scripts\python.exe -m pytest `
  tests/test_mcts_ai.py tests/test_heuristic_ai.py tests/test_minimax_ai.py `
  tests/test_tournament_runner.py tests/test_data_pipeline.py `
  tests/test_selfplay_generation.py -q -p no:cacheprovider `
  --basetemp pytest-cache-files-mcts-phase0
```

This attempt reached the tests but Windows denied access to pytest's temporary
directory during fixture setup/cleanup. It was an environment permission error,
not an assertion failure.

Approved rerun outside the sandbox:

```powershell
.\myenv\Scripts\python.exe -m pytest `
  tests/test_mcts_ai.py tests/test_heuristic_ai.py tests/test_minimax_ai.py `
  tests/test_tournament_runner.py tests/test_data_pipeline.py `
  tests/test_selfplay_generation.py -q -p no:cacheprovider `
  --basetemp pytest-cache-files-mcts-phase0-escalated
```

Result: **177 passed in 21.82s**.

Benchmark command, run sequentially for seeds 11, 22, and 33:

```powershell
.\myenv\Scripts\python.exe benchmarks\bench_mcts.py `
  --scenario midgame_mixed --seed <seed> --repeats 2
```

### Benchmark measurements

| Seed | Profile | Action | Score | Median ms | Sims/s |
|---:|---|---|---:|---:|---:|
| 11 | 100 | `(0, 0)` | 1.000 | 184.69 | 541.5 |
| 11 | 400 | `(8, 4)` | 0.857 | 689.41 | 580.2 |
| 11 | 1,000 | `(3, 6)` | 0.591 | 4,981.26 | 200.8 |
| 22 | 100 | `(0, 0)` | 1.000 | 203.46 | 491.5 |
| 22 | 400 | `(3, 0)` | 0.714 | 738.49 | 541.6 |
| 22 | 1,000 | `(2, 3)` | 0.476 | 1,491.23 | 670.6 |
| 33 | 100 | `(0, 2)` | 1.000 | 228.97 | 436.7 |
| 33 | 400 | `(6, 1)` | 0.857 | 864.25 | 462.8 |
| 33 | 1,000 | `(6, 1)` | 0.500 | 5,511.04 | 181.5 |

Each same-seed/profile decision was identical over two repeats. The benchmark
is reproducible logically, while latency varies because random rollouts can have
different lengths across seeds.

Machine-readable artifact:
`.benchmarks/mcts_upgrade/baseline/baseline.json`.

### Existing tournament evidence

From `Selfplay_2000_Recheck_Report.md`:

- Heuristic beat MCTS-20 in 666/666 games.
- Minimax-D2 beat MCTS-20 in 666/666 games.
- The full 2,000-game run was not repeated because the prompt explicitly avoids
  rerunning deterministic duplicate trajectories in Phase 0.

### Confirmed limitations

1. MCTS-20 never exhausts root actions in the observed games.
2. No root child is revisited at the dataset-v1 budget.
3. Random rollout has no tactical policy.
4. The current benchmark measures throughput, not playing strength.
5. Dataset-v1 deduplication hashes the target together with the position.

### Gate decision

Phase 0 passes: all 177 relevant tests pass, the required three-seed benchmark
is reproducible, and machine-readable evidence exists. Phase 1 is authorized.

### Files changed in this phase

- `.benchmarks/mcts_upgrade/baseline/baseline.json` (ignored generated evidence)
- `docs/data/MCTS_Upgrade_Execution_Report.md`

## Phase 1 — Tactical gate and progressive widening

**Status:** `passed`

### Files changed

- `core/agents/search_utils.py`
- `core/agents/mcts_ai.py`
- `tests/test_mcts_ai.py`
- `configs/benchmark_mcts_v2.json` (new versioned config; the old config is unchanged)
- `.benchmarks/mcts_upgrade/phase1/tree_stats.json`
- `docs/data/MCTS_Upgrade_Execution_Report.md`

### Implementation

- Added pure immediate-win and opponent-win detection using the exact
  `RuleEngine` blocked-end semantics.
- Added deterministic tactical pre-checks. Immediate win and unique forced block
  return `nodes=1`, `simulations=0`; the override is recorded in search stats.
- Added candidate tiers while preserving the full legal-action set.
- Added progressive widening with
  `min(|A|, max(1, ceil(c * (N + 1)^alpha)))`.
- Added legacy defaults (`legacy_random`, widening disabled, tactical pre-check
  disabled) so the Phase 0 implementation remains available for ablation.
- Added root visit and maximum-depth statistics without changing `AgentDecision`.

### Commands and tests

Focused development test:

```powershell
.\myenv\Scripts\python.exe -m pytest tests/test_mcts_ai.py -q -p no:cacheprovider
```

Result: **54 passed in 8.91s** after correcting one test-helper keyword
collision found by the first run.

Phase gate suite:

```powershell
.\myenv\Scripts\python.exe -m pytest `
  tests/test_mcts_ai.py tests/test_heuristic_ai.py tests/test_minimax_ai.py `
  tests/test_tournament_runner.py -q -p no:cacheprovider `
  --basetemp pytest-cache-files-mcts-phase1-escalated
```

Result: **184 passed in 18.46s**. A prior sandboxed attempt produced
183 passes plus one `tmp_path` setup error; the approved rerun proved that this
was the same Windows temporary-directory permission issue observed in Phase 0.

### Instrumented tree measurements

Scenario: `midgame_mixed`; seed: 11; `c=2.0`, `alpha=0.5`, tactical-local
candidate ordering.

| Sims | Root children | Max child visits | Mean visits/child | Max depth | Elapsed ms |
|---:|---:|---:|---:|---:|---:|
| 100 | 20 | 12 | 5.000 | 3 | 315.94 |
| 400 | 40 | 21 | 10.000 | 3 | 1,477.38 |
| 1,000 | 64 | 34 | 15.625 | 3 | 4,039.91 |

Machine-readable evidence:
`.benchmarks/mcts_upgrade/phase1/tree_stats.json`.

### Gate decision

Phase 1 passes. Tactical tests cover both players, all four directions, an edge
position, unique forced block, multiple opponent threats, and no false positive.
The instrumented runs prove root revisits and depth greater than two at every
required budget. All legacy contract tests remain green. Phase 2 is authorized.

### Known limitations

- Rollout is still the legacy uniform-random policy; changing it is Phase 2.
- Every simulation still clones the environment; optimization is Phase 2.
- Candidate tactical scanning is intentionally unoptimized pending profiling.

## Phase 2 — Guided rollout and performance optimization

**Status:** `passed`

### Files changed

- `core/agents/search_utils.py`
- `core/agents/mcts_ai.py`
- `tests/test_mcts_ai.py`
- `benchmarks/bench_mcts.py`
- `configs/benchmark_mcts_v2.json`
- `.benchmarks/mcts_upgrade/phase2/*.json`
- `docs/data/MCTS_Upgrade_Execution_Report.md`

### Implementation

- Added seeded epsilon tactical-local rollout with exact immediate-win and
  unique-block handling.
- Added validated `rollout_policy`, `rollout_epsilon`, and
  `reuse_simulation_env` options while retaining legacy defaults.
- Added clone-once plus balanced `undo()` back to the root as an ablatable
  optimization. Fixed-seed tests prove it matches per-simulation cloning.
- Removed the duplicate full-board legal scan during ranked expansion.
- Reused each node's stored candidate ordering.
- Added clone/selection/expansion/rollout timing, mean/max tree depth, root
  children, visit statistics, p95 latency, and JSON benchmark export.
- Tree reuse between real plies was intentionally not implemented; it is
  optional, adds reproducibility risk, and is not needed for teacher profiles.

### Tests

Focused suite after rollout and optimization:

```powershell
.\myenv\Scripts\python.exe -m pytest tests/test_mcts_ai.py -q -p no:cacheprovider
```

Result: **62 passed**.

Phase gate suite:

```powershell
.\myenv\Scripts\python.exe -m pytest `
  tests/test_mcts_ai.py tests/test_heuristic_ai.py tests/test_minimax_ai.py `
  tests/test_tournament_runner.py -q -p no:cacheprovider `
  --basetemp pytest-cache-files-mcts-phase2-escalated
```

Result: **192 passed in 22.00s**.

Tests prove tactical rollout behavior, fixed-seed rollout reproducibility,
clone-once equivalence, interrupt-safe rewind, input no-mutation, and unchanged
counter semantics.

### Performance evidence

Commands:

```powershell
.\myenv\Scripts\python.exe benchmarks/bench_mcts.py `
  --config configs/benchmark_mcts_v2.json `
  --profile MCTS-PHASE2-GUIDED --scenario midgame_mixed `
  --seed 11 --repeats 1 `
  --json .benchmarks/mcts_upgrade/phase2/guided_seed11.json

.\myenv\Scripts\python.exe benchmarks/bench_mcts.py `
  --config configs/benchmark_mcts_v2.json `
  --profile MCTS-PHASE2-OPT --scenario midgame_mixed `
  --seed 11 --repeats 2 `
  --json .benchmarks/mcts_upgrade/phase2/optimized_seed11.json
```

| Variant | Sims | Median ms | Sims/s | Clone ms | Expansion ms | Rollout ms |
|---|---:|---:|---:|---:|---:|---:|
| Guided, clone each | 100 | 680.75 | 146.9 | 0.61 | 120.62 | 552.50 |
| Guided, clone each | 400 | 3,721.72 | 107.5 | 3.00 | 693.87 | 2,988.22 |
| Guided, clone each | 1,000 | 20,932.83 | 47.8 | 15.02 | 3,767.23 | 16,917.35 |
| Guided, clone once | 100 | 769.65 | 129.9 | 0.01 | 134.27 | 622.11 |
| Guided, clone once | 400 | 4,300.80 | 93.0 | 0.00 | 763.57 | 3,459.98 |
| Guided, clone once | 1,000 | 20,231.83 | 49.4 | 0.01 | 3,622.75 | 16,213.76 |

Clone-once removes repeated clone cost and preserves logical results, but clone
was not the main bottleneck. Tactical rollout dominates total time and is more
expensive than legacy random rollout. A bounded-candidate rollout experiment
was measured and reverted because it lengthened rollouts and reduced throughput
further (1,000 simulations: 19.8 sims/s). The retained implementation is the
faster of the tested tactical-local variants.

### Gate decision

Phase 2 passes the explicit correctness and instrumentation gate: all tests are
green, guided rollout is seeded, clone-once is logically equivalent and safely
rewound, required timing/tree metrics are exported, and no budget/mutation
violation occurred. The throughput cost is accepted only for Phase 3 strength
qualification; it is not yet accepted as a teacher compute budget. If the
strength gain does not justify this cost, Phase 3 must fail or select a bounded
allowed configuration. Phase 3 is authorized.

### Known limitations

- Tactical-local rollout is compute-heavy.
- No inter-ply tree reuse is enabled.
- Strength has not yet been established; unit and throughput tests alone do not
  qualify the agent as a teacher.

## Phase 3 — Strength benchmark and teacher qualification

**Status:** `in_progress` — stopped before qualification; gate not passed

No training, self-play dataset generation, or data-pipeline mutation has been
performed. Phases 4 and 5 remain unauthorized.

### Files changed in this phase

- `benchmarks/eval_mcts_strength.py`
- `configs/benchmark_mcts_v2.json`
- `core/agents/mcts_ai.py` (scoped normalized rollout-horizon ablation)
- `core/agents/search_utils.py` (independent bounded line evaluator)
- `tests/test_mcts_ai.py`
- `.benchmarks/mcts_upgrade/phase3/*.json`
- `docs/data/MCTS_Upgrade_Execution_Report.md`

### Strength evaluator

The new evaluator uses `run_match()` with paired seeds and even side swapping.
It reports overall/as-X/as-O win/draw/loss, score rate, side difference,
mean/p95 move time, completed simulations, budget violations, hardware, profile
options, and JSON output.

### Ordered ablation results

All rows below used side-swapped games. Six-game rows used seed groups 11, 22,
and 33; two-game rows are preliminary seed-11 probes and are not qualification
evidence.

| Variant | Opponent | Sims | Games | W/D/L | Score rate | X/O score | Mean move ms | p95 ms |
|---|---|---:|---:|---|---:|---|---:|---:|
| Legacy | Heuristic | 20 | 6 | 0/0/6 | 0.000 | 0.000/0.000 | 42.35 | 76.44 |
| Legacy | Heuristic | 100 | 6 | 0/0/6 | 0.000 | 0.000/0.000 | 423.98 | 606.47 |
| Legacy | Heuristic | 400 | 6 | 0/0/6 | 0.000 | 0.000/0.000 | 2,118.63 | 2,775.64 |
| Legacy | Heuristic | 1,000 | 6 | 0/0/6 | 0.000 | 0.000/0.000 | 5,205.17 | 6,688.86 |
| Tactical pre-check only | Heuristic | 100 | 6 | 0/0/6 | 0.000 | 0.000/0.000 | 402.94 | 642.54 |
| Tactical + PW | Heuristic | 100 | 6 | 0/0/6 | 0.000 | 0.000/0.000 | 611.63 | 839.58 |
| Guided rollout | Heuristic | 100 | 2 | 2/0/0 | 1.000 | 1.000/1.000 | 2,936.60 | 6,289.62 |
| Guided + clone-once | Heuristic | 100 | 2 | 2/0/0 | 1.000 | 1.000/1.000 | 2,939.05 | 6,151.07 |
| Guided + clone-once | Minimax-D2 | 100 | 2 | 0/0/2 | 0.000 | 0.000/0.000 | 1,423.16 | 2,284.57 |
| Guided + clone-once | Minimax-D2 | 400 | 2 | 0/1/1 | 0.250 | 0.000/0.500 | 6,118.27 | 18,098.04 |
| Normalized horizon 20 | Heuristic | 100 | 2 | 1/1/0 | 0.750 | 1.000/0.500 | 2,019.88 | 4,116.50 |
| Normalized horizon 8 | Heuristic | 100 | 2 | 1/0/1 | 0.500 | 0.000/1.000 | 1,395.42 | 2,345.07 |

All completed benchmark artifacts report zero budget violations. The initial
six-game guided run was stopped after several minutes because its cost was much
higher than the earlier variants; it was replaced by the explicitly identified
two-game compute probe. No result from an interrupted run is reported as a
completed artifact.

### Post-change verification

```powershell
.\myenv\Scripts\python.exe -m pytest `
  tests/test_mcts_ai.py tests/test_heuristic_ai.py tests/test_minimax_ai.py `
  tests/test_tournament_runner.py -q -p no:cacheprovider `
  --basetemp pytest-cache-files-mcts-status-escalated
```

Result: **195 passed in 7.54s**.

Additional checks:

- `git diff --check`: pass;
- `configs/benchmark_mcts_v2.json`: valid JSON;
- modified/new Python modules: `py_compile` pass;
- no Python benchmark process remains running.

### Code-state interpretation

- `MCTSAgent()` remains backward compatible. Its defaults are still
  `tactical_precheck=False`, `candidate_policy="legacy_random"`,
  `rollout_policy="random"`, no progressive widening, and no rollout horizon.
- `configs/selfplay_w56_dataset_v1.json` still requests only 20 simulations and
  does not enable upgraded options. Rerunning dataset v1 therefore still uses
  legacy MCTS-20 and should be expected to reproduce the old imbalance.
- Upgraded behavior exists only through explicit options/profiles in
  `configs/benchmark_mcts_v2.json`.
- The hard-label/data-pipeline imbalance is not fixed yet because Phases 4 and 5
  were not authorized.

### Gate assessment

| Required Phase 3 gate | Current evidence | Status |
|---|---|---|
| Tactical win/block 100% | covered by passing tactical tests | pass |
| >=70% vs legacy over 200 games | not run | not passed |
| X/O difference <=10 points | tiny guided Heuristic probe passes; horizon and Minimax probes fail | not passed |
| >=35% vs Heuristic over 200 games | only 2-game guided probe | not passed |
| >=35% vs Minimax-D2 over 200 games | 0% at 100 sims; 25% at 400 sims in two-game probes | not passed |
| Stability over 3 seed groups | not run for candidate profile | not passed |
| Contract/budget | 195 tests pass; zero pilot violations | pass |

Phase 3 is not passed. In particular, the best completed Minimax probe is below
the 35% teacher threshold and has a 50-point side gap. The required 200-game
qualification was not run. Therefore MCTS is **not qualified as a teacher**, and
no dataset balancing, soft-label generation, full self-play run, or training is
authorized.

### Remaining Phase 3 work (not executed)

- Complete bounded 1,000-simulation and allowed exploration/PW/epsilon tuning
  only if the compute cost is accepted.
- Select a candidate only after pilot evidence against both Heuristic and
  Minimax-D2.
- Run 200 games per opponent across at least three seed groups.
- Run the 200-game comparison against legacy MCTS-20.
- Re-run the final gate suite with the frozen profile.

## Phase 4 — Pilot self-play and hard-label correction

**Status:** `not_started`

## Phase 5 — Soft policy targets and full dataset v2

**Status:** `not_started`
