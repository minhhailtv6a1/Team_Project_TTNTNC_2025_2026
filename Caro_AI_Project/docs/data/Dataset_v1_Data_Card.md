# Dataset v1 Data Card — three-agent self-play (2,000 games)

## Handoff summary for M1

| Item | Value |
|---|---|
| Dataset path | `data/processed_tensors/dataset_v1_three_agents_2000/` |
| Dataset version | `dataset-v1-three-agents-2000` |
| Contract | `caro-v2`, board 11×11, win length 5 |
| Raw run ID | `w56-dataset-v1-three-agents-2000` |
| Split | 1,400 / 300 / 300 games: train / validation / test |
| Encoder | `[current_player, opponent, legal]`, `float32` |
| Augmentation | Eight D4 transforms on train only |
| Checkpoint-selection rule | Use validation only; open test once after model/config selection is frozen |

M1 must not parse raw JSONL in the train loop. Use the public loader:

```python
from core.ml.data_pipeline import load_dataset_split

dataset_dir = "data/processed_tensors/dataset_v1_three_agents_2000"
train = load_dataset_split(dataset_dir, "train")
val = load_dataset_split(dataset_dir, "val")
test = load_dataset_split(dataset_dir, "test")

# train["x"]          -> float32 [N, 3, 11, 11]
# train["legal_mask"] -> bool    [N, 121]
# train["target"]     -> int64   [N]
```

The loader verifies the tensor SHA-256 from `dataset_manifest.json`, checks
shape/dtype and rejects any target outside its legal mask. Pass
`verify_checksum=False` only for explicitly approved local debugging.

## Provenance and collection

The source is self-play, not human expert play. The raw run contains 2,000
complete `GameRecord` objects in `caro-v2` JSONL:

| Pair | Games | Side balancing |
|---|---:|---|
| Heuristic vs Minimax | 668 | 334 games per X assignment |
| Heuristic vs MCTS | 666 | 333 games per X assignment |
| Minimax vs MCTS | 666 | 333 games per X assignment |

Teacher settings were Heuristic (no search budget), Minimax with Alpha-Beta at
depth 2, and MCTS with 20 simulations. The raw manifest records seed policy,
agent constructors, hardware and raw shard checksum. All valid games in the
declared run were retained; no game was selected by winner.

Observed raw outcomes: Heuristic won 1,000 / lost 0 / drew 334; Minimax won
666 / lost 334 / drew 334; MCTS won 0 / lost 1,332 / drew 0. These outcomes
are descriptive only, not an Elo evaluation.

## Processing

Every raw game was replayed from an empty `CaroEnv`. Before every move, the
pipeline creates one sample from the current player perspective:

- channel 0: current player stones;
- channel 1: opponent stones;
- channel 2: currently legal cells;
- label: `row * 11 + col` for the actual teacher move.

Games, not individual states, were split deterministically with seed
`20261107`: 70% train, 15% validation, 15% test. Dedup hashes
`(encoded_state, legal_mask, target)`, prioritizes train, then removes copies
from validation and test to prevent cross-split sample leakage. D4 rotation
and reflection are applied only after that split, and only to train.

| Split | Games | Samples before dedup | Duplicates removed | Exported samples |
|---|---:|---:|---:|---:|
| Train | 1,400 | 46,488 | 37,696 | 70,336 |
| Validation | 300 | 10,034 | 8,201 | 1,833 |
| Test | 300 | 11,120 | 9,547 | 1,573 |

The train export count is higher because 8,792 unique train samples receive
eight D4 variants. Validation and test are never augmented. Game-ID overlap
between splits is zero.

## Artifact checksums

| Artifact | SHA-256 |
|---|---|
| `train.npz` | `136bafb372187c6c0c1ca33225e97fc6426391c21f7c685dd80461c783ab77b2` |
| `val.npz` | `7860de01a842c8a5642260b7fb2cda9ae1256b1be79974e6fa8dc8797f92a2ff` |
| `test.npz` | `a9d4882602bb1ced652225d7222916c6f8ada2174709c87824d26a0d159fd7e4` |
| `split_game_ids.json` | `5db6cb0f3bb99caeb3246910616884a2f9b12b3a35d4d123006c84af23615ea0` |
| `validation_report.json` | `dd069299d9756a6bf87ab2aaa973ef037f06810592d7b3488df5ada8c495eeaf` |
| Raw `shard_000.jsonl` | `3d1088882ba09701c70f82af2232a0fd55e378f26eb1a3da8bcaed16be5a727e` |

`dataset_manifest.json` is the source of truth for all artifact checksums;
verify it before any production training run.

## Limitations and intended use

- Labels imitate three programmatic teachers and can inherit their biases.
- MCTS was markedly weaker at this budget, so teacher quality is unbalanced.
- High duplicate removal shows limited trajectory diversity; do not interpret
  the augmented count as that many independent positions.
- The dataset supports supervised policy learning and contract smoke tests;
  it is not evidence of human-level play or reinforcement learning.
- Do not tune architecture, learning rate, epoch count or checkpoint using
  the test split.

## Reproduction

```powershell
python scripts/build_dataset.py `
  --input data/raw_logs/w56_selfplay_dataset_v1 `
  --output data/processed_tensors/dataset_v1_three_agents_2000 `
  --config configs/train_w56.json
```

The build validates raw-shard checksums and replay invariants before writing
any processed tensor. Generated logs and tensors are intentionally ignored by
Git; commit this card, configs, code and tests instead.
