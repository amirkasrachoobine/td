# Tower Defense

A small 2D tower defense game in Python and pygame.

## Run it (Fedora)

```sh
sudo dnf install python3-pygame
python3 run.py
```

Or in a virtualenv: `python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt && python run.py`

## How to play

Enemies walk the dirt path from left to right. Each one that gets through costs lives
(brutes cost 3). Build towers on the grass, then send the next wave.

| Input | Action |
|---|---|
| `1` / `2` / `3` or sidebar buttons | pick Arrow / Cannon / Frost tower |
| Left click | place the picked tower, or select an existing one |
| Shift + click | place several towers in a row |
| Right click / `Esc` | cancel |
| `U` / `S` | upgrade / sell the selected tower (sell refunds 70%) |
| `Space` | send the next wave |
| `F` | toggle 2x speed |
| `P` | pause |
| `R` | restart after game over |

**Towers:** Arrow (cheap, fast, single target), Cannon (slow, splash damage),
Frost (light damage, slows). Each upgrades twice.

**Enemies:** Grunt (basic), Runner (fast, from wave 2), Brute (slow and tough, from wave 4).
HP grows every wave; clearing a wave pays a gold bonus.

## Code

- `td/config.py` — map path, tower/enemy stats, wave composition. Balance lives here.
- `td/game.py` — game rules and simulation, no pygame (testable headless).
- `td/main.py` — pygame drawing and input.
- `tests/` — `python3 -m unittest discover tests`
