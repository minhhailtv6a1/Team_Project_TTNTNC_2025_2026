# Execution prompt — MCTS upgrade and label balancing

Copy the prompt below into the implementation agent. Run it from the repository
root. The prompt intentionally contains strict phase gates and scope limits so
the agent cannot skip ahead or introduce unrelated work.

---

## Prompt

You are the implementation agent for the `Caro_AI_Project` repository.

Your objective is to implement the MCTS upgrade and dataset-label correction
plan in the exact order defined by:

`docs/data/MCTS_Upgrade_and_Label_Balance_Plan.md`

Read that file completely before changing any code. Also read:

- `docs/data/Selfplay_2000_Recheck_Report.md`
- `configs/benchmark.json`
- `configs/selfplay_w56_dataset_v1.json`
- `core/agents/mcts_ai.py`
- `core/agents/heuristic_ai.py`
- `core/agents/minimax_ai.py`
- `core/utils/tournament_runner.py`
- `scripts/generate_selfplay.py`
- `core/ml/data_pipeline.py`
- `tests/test_mcts_ai.py`
- `tests/test_data_pipeline.py`

The plan document is the source of truth. If this prompt and the plan appear to
conflict, follow the plan and record the conflict in the execution report.

### Primary outcome

Deliver an upgraded, reproducible MCTS that:

1. handles immediate wins and forced blocks;
2. uses progressive widening so UCT actually revisits promising children;
3. uses a seeded tactical-local rollout policy;
4. is profiled and benchmarked for correctness, speed, and playing strength;
5. is allowed to generate training data only after passing the defined teacher
   quality gate;
6. produces a versioned dataset pipeline that detects position leakage,
   conflicting labels, source imbalance, and low-quality labels;
7. supports weighted hard targets first, then MCTS visit-distribution soft
   targets without overwriting dataset v1.

Do not perform unrelated refactors, UI work, API work, model architecture work,
dependency upgrades, formatting sweeps, or documentation rewrites.

## Non-negotiable working rules

1. Inspect repository instructions and the current working tree before editing.
   Preserve all pre-existing user changes and untracked files.
2. Do not modify, delete, rename, or regenerate dataset v1 artifacts or its
   committed data card.
3. Do not overwrite existing configs. Create explicitly versioned new configs.
4. Do not change `caro-v2` public behavior unless the relevant phase explicitly
   requires an additive, backward-compatible extension.
5. Prefer an auxiliary sidecar schema for search statistics and opening metadata
   over breaking `MoveRecord` or `GameRecord`.
6. Keep all random behavior local to the supplied seed. Never call
   `random.seed()` globally.
7. Preserve the Agent contract: legal action, no mutation of the input
   environment, deterministic result for the same state/config/budget/seed, and
   correct node/simulation counters.
8. Add tests before or with every behavioral change. Do not weaken, delete, or
   skip an existing test to make a phase pass.
9. Do not lower a quality threshold after seeing poor results. If a gate fails,
   tune only the parameters allowed in that phase and rerun it. If the planned
   variants still fail, stop and report the evidence.
10. Do not start a later phase until every mandatory gate in the current phase
    passes.
11. Do not generate the full dataset until the strength and pilot-data gates
    pass.
12. Do not claim success from unit tests alone. Report the actual commands,
    configs, seeds, game counts, results, latency, and output paths.
13. Do not create commits, push branches, open pull requests, or alter Git
    configuration unless the user separately requests it.
14. Keep generated logs, benchmark artifacts, and tensors in the existing
    ignored artifact/data locations. Do not commit large generated files.
15. Work only on files listed in the applicable phase. If another file is truly
    required, explain why in the execution report before editing it.

## Required progress report

Create and continuously update:

`docs/data/MCTS_Upgrade_Execution_Report.md`

For every phase, record:

- status: `not_started`, `in_progress`, `passed`, `failed`, or `blocked`;
- files changed;
- exact commands run;
- config and seeds used;
- measured results;
- gate decision and evidence;
- known limitations;
- whether the next phase is authorized by the gate.

Never mark a phase `passed` without attaching the corresponding test or
benchmark evidence.

## Phase 0 — Freeze and reproduce the baseline

Do not change implementation code in this phase.

### Tasks

1. Inspect the working tree and repository instructions.
2. Run the existing MCTS, Heuristic, Minimax, tournament, and data-pipeline tests
   that are relevant to this work.
3. Reproduce the current MCTS benchmark at 100, 400, and 1,000 simulations using
   the existing `benchmarks/bench_mcts.py` and seeds 11, 22, and 33.
4. Record the existing MCTS-20 tournament failure from the checked-in recheck
   report. Do not rerun 2,000 games merely to reproduce deterministic duplicate
   trajectories.
5. Store machine-readable baseline benchmark results in an artifact path such
   as `artifacts/mcts_upgrade/baseline/`.
6. Record the current limitations:
   - MCTS-20 never exhausts root actions in the observed games;
   - no root child is revisited;
   - random rollout has no tactical policy;
   - throughput benchmark does not measure playing strength;
   - dataset dedup includes the target in its hash.

### Phase 0 gate

Pass only if the relevant existing tests pass and the baseline results are
reproducible. If failures are caused by environment permissions rather than code,
rerun with a workspace-local temporary directory and document the distinction.

Do not make algorithm changes until this gate passes.

## Phase 1 — Tactical gate and progressive widening

Allowed primary files:

- `core/agents/mcts_ai.py`
- `core/agents/search_utils.py` (new, if needed)
- `tests/test_mcts_ai.py`
- `configs/benchmark.json`
- `docs/data/MCTS_Upgrade_Execution_Report.md`

### Step 1A — Add a pure tactical helper

Implement a read-only helper that can identify:

- immediate winning actions for the current player;
- immediate winning actions for the opponent;
- a unique forced block;
- multiple unanswerable threats.

The helper may reuse low-level pattern scanning, but it must not make the entire
MCTS decision through `HeuristicAgent.action_priority()`. Keep rule-level
win/block detection separate from policy ranking to avoid making all teachers
identical.

Add tests for horizontal, vertical, both diagonals, both players, edge positions,
multiple winning actions, forced block, and no false positive. The helper must
not mutate the board or environment.

### Step 1B — Add tactical pre-check to MCTS

Before tree search:

1. return an immediate win deterministically;
2. return the unique forced block deterministically;
3. otherwise continue into MCTS with urgent threats ranked first.

The returned `AgentDecision` must still have valid counters and elapsed time.
Define and test the counter semantics for tactical overrides.

### Step 1C — Add candidate tiers and progressive widening

Keep the full legal-action set available, but rank it in this order:

1. immediate win/block;
2. actions within Chebyshev radius 2 of existing stones;
3. threat-creating or threat-blocking actions;
4. remaining legal actions in seeded order.

Implement:

```text
allowed_children(N) = min(|A|, max(1, ceil(c_pw * (N + 1)^alpha)))
```

Add constructor options with strict validation:

- `tactical_precheck`;
- `candidate_policy`;
- `neighbor_radius`;
- `progressive_widening_c`;
- `progressive_widening_alpha`.

Preserve a legacy configuration so the original implementation remains
available for ablation. Do not silently reinterpret the existing MCTS-20
baseline.

### Required Phase 1 tests

- immediate win accuracy is 100%;
- forced block accuracy is 100%;
- root child visits become greater than 1 under an adequate budget;
- maximum tree depth reaches at least 2 in opening and midgame scenarios;
- progressive widening never exceeds legal actions or the node budget;
- remaining actions can eventually be opened;
- same state/config/budget/seed returns the same result;
- no input-environment mutation;
- global RNG state is unchanged;
- all old MCTS contract tests still pass.

### Phase 1 gate

Pass only if all relevant unit tests pass and an instrumented 100/400/1,000
simulation run proves that UCT revisits root children. Record root-child count,
maximum child visits, mean visits/child, and maximum tree depth.

Do not implement guided rollout until this gate passes.

## Phase 2 — Guided rollout and performance optimization

Allowed primary files:

- the Phase 1 files;
- `benchmarks/bench_mcts.py`;
- benchmark-specific tests if present;
- `docs/data/MCTS_Upgrade_Execution_Report.md`.

### Step 2A — Seeded tactical-local rollout

Implement the following rollout policy:

```text
if an immediate win exists:
    choose it
else if a unique forced block exists:
    choose it
else with probability 1 - epsilon:
    choose a seeded tactical-local action
else:
    choose a seeded random legal action
```

Add validated options:

- `rollout_policy`;
- `rollout_epsilon`.

Initial experiment values:

- teacher candidate: epsilon 0.15;
- diversity evaluation: epsilon 0.25.

Do not add a truncated rollout that returns an arbitrary zero. A rollout horizon
is allowed only if a separately tested leaf evaluation is normalized to `[-1,1]`
and included as an explicit ablation.

### Step 2B — Profile before optimizing

Extend the benchmark to measure, as far as practical:

- median and p95 move time;
- simulations per second;
- root children and visit distribution;
- mean and maximum tree depth;
- time spent in clone, legal-action generation, selection, expansion, and
  rollout.

Export JSON in addition to readable console output.

### Step 2C — Optimize clone/legal-action overhead

Apply optimizations separately so regressions can be isolated:

1. reuse one simulation environment with balanced `step()/undo()` back to root;
2. avoid duplicate `legal_actions()` calls inside expansion;
3. cache candidate ordering at the node level where safe.

For each optimization, prove:

- the input environment and its undo history are unchanged;
- fixed seed/config produces the same logical result as before the optimization;
- simulation/node counters remain correct;
- performance is measured before and after.

### Step 2D — Tree reuse is optional and last

Do not implement tree reuse before Steps 2A–2C pass. If implemented:

- reuse only when the observed state is a verified descendant of the previous
  root;
- reset on identical repeated calls, state-key mismatch, config change, seed
  change, or budget-profile change;
- keep `reuse_tree = false` for reproducible dataset/evaluation profiles;
- add a test proving repeated calls on the same state remain deterministic.

### Phase 2 gate

Pass only if:

- tactical and contract tests remain green;
- guided rollout is deterministic for a fixed seed;
- optimization does not change fixed-seed logical results unexpectedly;
- the benchmark report includes the required tree and timing metrics;
- no budget or mutation violation is observed.

Do not run strength qualification until this gate passes.

## Phase 3 — Strength benchmark and teacher qualification

Allowed primary files:

- `benchmarks/eval_mcts_strength.py` (new);
- `configs/benchmark.json`;
- MCTS/config/test files only if a measured failure requires a scoped fix;
- `docs/data/MCTS_Upgrade_Execution_Report.md`.

### Step 3A — Add a strength evaluator

Use the existing `run_match()` and side-swapping protocol. The evaluator must:

- use paired seeds;
- swap X/O evenly;
- report win/draw/loss;
- report score rate `(wins + 0.5 * draws) / games`;
- report results overall, as X, and as O;
- report side score-rate difference;
- report median/p95 move latency and completed simulations;
- export machine-readable JSON;
- include agent options, budget, seed set, hardware, and code/config paths.

### Step 3B — Run ablations in this exact order

1. legacy MCTS at 20, 100, 400, and 1,000 simulations;
2. tactical gate only;
3. tactical gate plus progressive widening;
4. add tactical-local rollout;
5. add clone/undo optimization with unchanged search logic;
6. tune exploration weight only after the earlier effects are measured;
7. evaluate tree reuse last and never enable it for teacher qualification.

Change one factor at a time. Do not launch an unbounded grid search.

Allowed tuning ranges after the initial ablation:

- simulations: 400, 1,000, then 2,000 only if necessary;
- exploration weight: 0.7, 1.0, and sqrt(2);
- progressive widening `c`: 1.5, 2.0, 2.5;
- progressive widening `alpha`: 0.4, 0.5, 0.6;
- rollout epsilon: 0.15 and 0.25.

Use staged one-factor-at-a-time tuning. Stop exploring a parameter when it is
clearly dominated in both strength and compute.

### Step 3C — Mandatory game counts and seeds

Use at least 200 games per matchup for pilot qualification, evenly side-swapped,
across at least three seed groups. Evaluate upgraded MCTS against:

- legacy MCTS-20;
- `HeuristicAgent`;
- `MinimaxAgent` with Alpha-Beta and depth 2.

Do not use the full 2,000-game dataset run as a tuning loop.

### Phase 3 quality gates

All conditions are mandatory:

| Gate | Required result |
|---|---|
| Tactical | 100% immediate-win and forced-block accuracy |
| Versus legacy MCTS-20 | upgraded MCTS score rate >= 70% over at least 200 games |
| Side balance | X/O score-rate difference <= 10 percentage points |
| Teacher eligibility vs Heuristic | score rate >= 35% |
| Teacher eligibility vs Minimax-D2 | score rate >= 35% |
| Stability | conclusions hold across at least three seed groups |
| Contract | zero illegal actions, mutation errors, or budget violations |

If either teacher-eligibility gate fails, do not proceed to dataset generation.
Continue only with the bounded Phase 3 tuning ranges. If those variants fail,
mark Phase 3 `failed`, document the best result, and stop. Do not lower the
threshold or disguise failure by changing opponents.

## Phase 4 — Versioned pilot self-play and hard-label correction

This phase is authorized only after Phase 3 passes.

Allowed primary files:

- `scripts/generate_selfplay.py`;
- a new versioned self-play config such as
  `configs/selfplay_dataset_v2.json`;
- raw sidecar helpers/schema under the existing data or utility modules;
- `core/ml/data_pipeline.py`;
- `tests/test_selfplay_generation.py`;
- `tests/test_data_pipeline.py`;
- a new versioned train config;
- `docs/data/MCTS_Upgrade_Execution_Report.md`.

### Step 4A — Add seeded random openings

Implement deterministic random opening prefixes with validated config fields:

- opening length selected from 2, 4, or 6 plies;
- actions constrained to a configurable center radius;
- reject terminal openings and openings with an immediate forced win;
- use paired openings for side-swapped games;
- include opening actions in raw replay history;
- record `opening_plies` and opening metadata in a checksummed sidecar or an
  explicitly versioned additive schema;
- exclude opening-prefix moves from teacher targets.

Do not let the current pipeline misattribute random opening actions to the X/O
agents.

### Step 4B — Record search statistics without breaking `caro-v2`

Prefer a checksummed `search_stats.jsonl` sidecar keyed by `(game_id, ply)`.
For MCTS moves, record at least:

- legal/candidate counts;
- root visit counts by action;
- selected action and selected visit ratio;
- policy entropy;
- maximum tree depth;
- tactical override flag;
- simulations and budget profile;
- MCTS implementation/profile version.

Validate one-to-one alignment between raw MCTS moves and sidecar records.

### Step 4C — Implement dataset v1.1 hard-label safeguards first

Before soft targets, add backward-compatible support for:

- `position_hash = hash(encoded_state, legal_mask)`;
- `label_hash = hash(position_hash, target)`;
- position-level cross-split leakage detection;
- conflicting-target reporting for the same position;
- tactical quality flags;
- optional `sample_weight: float32`;
- breakdowns by source, matchup, outcome, side, game phase, and tactical flag;
- source share before filtering, after filtering, after dedup, after split, and
  after augmentation.

Apply quality filtering before source balancing:

- reject invalid replay/checksum/schema records;
- reject or strongly downweight missed immediate wins;
- reject or strongly downweight missed unique forced blocks;
- reject budget-violation games when configured;
- do not discard every move from a losing game;
- do not oversample a teacher that failed the quality gate.

Initial candidate weights, implemented as validated config rather than hidden
constants:

- win: 1.0;
- draw: 0.75;
- loss without tactical blunder: 0.5;
- tactical blunder: 0.1 or reject;
- source weight: target share / observed share, clipped to `[0.5, 2.0]`;
- final weight clipped to `[0.25, 4.0]`.

Extend the public loader additively so existing dataset v1 files containing only
`x`, `legal_mask`, and `target` continue to load.

### Step 4D — Generate only a pilot

Generate 300–600 games, not the full dataset. Use simulation-limited MCTS with
`reuse_tree = false`; do not use a hardware-dependent time limit.

Run full replay, schema, checksum, sidecar-alignment, quality, dedup, leakage,
and distribution validation.

### Phase 4 pilot gates

| Gate | Required result |
|---|---|
| Replay/schema/checksum | 100% pass |
| Cross-split game overlap | 0 |
| Cross-split position overlap | 0 |
| Illegal target | 0 |
| Unflagged tactical blunder | 0 |
| Side sample imbalance | <= 10 percentage points |
| Duplicate rate | target < 30%; otherwise stop and analyze openings |
| Source distribution | reported after every processing stage |
| Label conflicts | count, entropy, sources, and top positions reported |

If the pilot fails, fix only the responsible opening/data-pipeline issue and
rerun the pilot. Do not generate the full dataset.

## Phase 5 — Soft policy targets and full dataset v2

This phase is authorized only after the Phase 4 pilot passes.

### Step 5A — Implement soft targets

For MCTS search records, build:

```text
pi(a) = N(a)^(1 / temperature) / sum_b N(b)^(1 / temperature)
```

Requirements:

- illegal actions have probability zero;
- each policy target sums to 1 within numerical tolerance;
- temperature is versioned and configurable by game phase;
- MCTS contributes its root visit distribution;
- Heuristic and Minimax may contribute one-hot distributions;
- samples sharing a `position_hash` are aggregated using quality/source weights;
- conflict entropy and teacher agreement are reported;
- hard-target dataset loading remains backward compatible.

Export a versioned schema containing, as applicable:

- `x`;
- `legal_mask`;
- `policy_target: float32[N,121]`;
- `sample_weight: float32[N]`;
- metadata and checksums.

Do not silently replace `target: int64` in the old schema. The manifest must
declare whether an artifact is hard-target or soft-policy.

### Step 5B — Generate and validate the full dataset

Only after the soft-target tests and a second pilot pass:

1. freeze MCTS code, config, seeds, opening policy, sidecar schema, and dataset
   config;
2. generate a new raw run ID;
3. build the new versioned dataset directory;
4. run all replay, checksum, legality, leakage, conflict, source, side, phase,
   dedup, and weight validations;
5. create `docs/data/Dataset_v2_Data_Card.md` with provenance, exact commands,
   outcomes, distributions, limitations, checksums, and intended use;
6. keep the test split closed for later model evaluation.

### Phase 5 final gates

- all relevant repository tests pass;
- all Phase 3 strength gates still pass with the frozen teacher config;
- all Phase 4 data-quality gates pass on the full run;
- source share after quality filtering and dedup is 25–40% per teacher, or the
  deviation is explicitly justified because a teacher was intentionally
  downweighted;
- no position-level split leakage;
- no illegal or non-normalized policy target;
- manifest and every artifact checksum verify;
- dataset v1 remains unchanged and loadable.

## Required config profiles

Create versioned profiles after their implementation is validated:

| Profile | Purpose | Simulations | Time limit | Reuse tree |
|---|---|---:|---|---|
| `MCTS-SMOKE` | tests/integration | 64 | none | false |
| `MCTS-UI` | interactive use | 100–200 | 150–300 ms | optional after tests |
| `MCTS-EVAL-400` | controlled ablation | 400 | none | false |
| `MCTS-EVAL-1000` | strength evaluation | 1,000 | none | false |
| `MCTS-TEACHER` | data generation | 1,000; 2,000 only if required by gate | none | false |

The teacher profile must use fixed simulations/nodes, never wall-clock stopping.

## Scope by file

Expected files are limited to:

- `core/agents/mcts_ai.py`;
- `core/agents/search_utils.py` if needed;
- `tests/test_mcts_ai.py`;
- `benchmarks/bench_mcts.py`;
- `benchmarks/eval_mcts_strength.py`;
- `configs/benchmark.json`;
- new versioned self-play/train configs;
- `scripts/generate_selfplay.py`;
- narrowly scoped raw-sidecar utilities/schema;
- `core/ml/data_pipeline.py`;
- `tests/test_selfplay_generation.py`;
- `tests/test_data_pipeline.py`;
- `docs/data/MCTS_Upgrade_Execution_Report.md`;
- `docs/data/Dataset_v2_Data_Card.md` after the full run.

Do not touch UI, API, unrelated agents, neural-network architecture, deployment,
or unrelated documentation unless a concrete compile/test failure proves it is
necessary. If that happens, document the dependency and make the smallest
possible change.

## Mandatory final response

When the work stops—whether complete, failed at a gate, or blocked—respond with:

1. the last phase reached and its status;
2. a concise list of files changed;
3. exact tests and benchmarks run, with pass/fail counts;
4. strength results by opponent and side;
5. dataset pilot/full-run validation metrics if reached;
6. artifact, config, report, and data-card paths;
7. any gate that failed and the evidence;
8. remaining work that is strictly part of this plan.

Do not report a later phase as complete when an earlier gate failed. Do not add
optional unrelated next steps.

Begin with Phase 0 only.

---
