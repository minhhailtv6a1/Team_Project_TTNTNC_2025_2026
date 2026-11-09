# Raw self-play schema v1

`caro-w56-raw-v1` is the Week 5 raw-data profile. It uses the existing
`caro-v2` `GameRecord` JSONL serializer; one UTF-8 JSON object represents one
complete game. The only accepted contract version is `caro-v2`.

## Required game object

| Field | Type / rule |
|---|---|
| `contract_version` | exactly `"caro-v2"` |
| `game_id` | non-empty, run-stable string; production IDs derive from run ID, seed, side assignment and game index |
| `config` | `{"board_size": 11, "win_length": 5}` |
| `seed` | integer or `null` |
| `x_agent`, `o_agent` | non-empty agent labels |
| `moves` | ordered list of complete move objects |
| `terminated` | `true` for data admitted to the pipeline |
| `winner` | `1`, `-1`, or `null` for a draw |

Each move object has `ply` (continuous, starting at 1), `player` (`1` for X,
`-1` for O), `action` (`[row, col]`, zero-based), `reward`, `elapsed_ms`,
`nodes`, and `simulations`. Actions must be unique, in bounds and legal at the
time of replay. Metrics must be non-negative.

No board state or tensor is stored in raw JSONL. Consumers recreate the state
before each action by replaying from an empty `CaroEnv`, and reject a game if
the replayed player, reward, terminal flag or winner differs from its record.

## Fixture and encoder hand-off

`tests/fixtures/w56_selfplay_one_game.jsonl` is a complete, deterministic
11×11 game: X (`HeuristicAgent`) wins at ply 9. Before ply 7, X is to move;
X owns `(5,2)`, `(5,3)`, `(5,4)`, O owns `(0,0)`, `(0,2)`, `(0,4)`, and the
label action is `(5,5)`. This is the shared M1/M3 state/action fixture for the
three-channel encoder; its target index is `5 * 11 + 5 = 60`, and the target
is legal.

The fixture is intentionally small and may be committed. Pilot and production
raw logs belong under `data/raw_logs/` and must not be committed.
