# Tower Defense

A small 2D tower defense game in Python and pygame.

## Run it (Fedora)

```sh
sudo dnf install python3-pygame
python3 run.py
```

Or with pip in a virtualenv (often faster than dnf, since it skips dnf's repo metadata refresh).
This installs [pygame-ce](https://pyga.me), a drop-in fork of pygame that ships prebuilt wheels
for new Pythons such as 3.14, so nothing has to compile:

```sh
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python run.py
```

### If installs are slow

- **dnf**: let it pick the fastest mirror and download in parallel by adding these lines
  under `[main]` in `/etc/dnf/dnf.conf`:

  ```ini
  fastestmirror=True
  max_parallel_downloads=10
  ```

  Then run `sudo dnf clean metadata` once and install again.
- **pip**: point it at a PyPI mirror close to you with `-i`, e.g.
  `pip install -i https://<mirror>/simple -r requirements.txt`, or set it permanently with
  `pip config set global.index-url https://<mirror>/simple`.

## How to play

The game opens on a menu: pick one of three maps (Village Road, Farmland, Riverside)
and a difficulty, then press Start or Enter. Arrow keys also change the choice.

| Difficulty | Enemy health | Enemy speed |
|---|---|---|
| Easy | x0.75 | x0.85 |
| Normal | x1 | x1 |
| Hard | x1.5 | x1.25 |


Enemies walk the dirt path from left to right. Each one that gets through costs lives
(brutes cost 3). Build towers on the grass, then send the next wave.

| Input | Action |
|---|---|
| `1`–`6` or sidebar buttons | pick Arrow / Cannon / Frost / Fire / Arcane / Lightning tower |
| Left click | place the picked tower, or select an existing one |
| Shift + click | place several towers in a row |
| Right click / `Esc` | cancel |
| `U` / `S` | upgrade / sell the selected tower (sell refunds 70%) |
| `Space` | send the next wave |
| `F` | toggle 2x speed |
| `P` | pause |
| `M` | back to the menu |
| `R` | play the same map again after game over |

**Towers:** Arrow (cheap, fast, single target), Cannon (slow, splash damage),
Frost (light damage, slows), Fire (sets enemies burning), Arcane (long range, heavy
hits) and Lightning (chains between nearby enemies). Each upgrades twice, and the tower's
look changes with its level.

**Enemies** come in four factions, one per wave in turn: Humans, Elves, Goblins,
Skeletons. Every faction has six units: Soldier (basic), Spearman (sturdier, from
wave 2), Cavalry (fast, from wave 2), Archer (quick and fragile, from wave 3), Elite
(slow and tough, from wave 4) and Champion (a boss every fifth wave).
HP grows every wave; clearing a wave pays a gold bonus.

## Code

- `td/config.py` — map path, tower/enemy stats, wave composition. Balance lives here.
- `td/game.py` — game rules and simulation, no pygame (testable headless).
- `td/main.py` — pygame drawing and input.
- `td/mapart.py` — paints the map: pixel grass, the dirt road along the enemy path, and
  the river and bridges, and the scenery. Each map's path, river and scenery are in
  `MAPS` in `config.py` (towers can't be built on the path, scenery or water);
  difficulties are in `DIFFICULTIES`.
- `assets/enemies/` — `<faction>_<unit>.png`, all facing right; the game mirrors them
  when an enemy walks left.
- `assets/fx/` — bullet sprites (`<tower>_shot_0.png`, flying left in the art; the game
  turns them toward their target), hit animations (`<tower>_hit_<frame>.png`) and the
  flames on burning enemies (`burn_<frame>.png`). Sizes are set at the top of `td/main.py`.
- `assets/map/` — scenery sprites (houses, trees, well, fences, stalls, …).
- `assets/towers/` — tower sprites, one PNG per look (transparent background).
  `config.py` says which sprite each tower level uses.
- `tests/` — `python3 -m unittest discover tests`
