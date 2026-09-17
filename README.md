# F1 Season Simulator

A Python simulator for F1 seasons: practice, qualifying (Q1/Q2/Q3), races,
points, championships, and an off-season driver transfer market — starting
from the real 2026 grid (11 teams, 22 drivers, Cadillac's debut, Audi's
works entry).

## Run it

```bash
cd f1_simulator
python3 main.py                       # 1 season, full race-by-race detail
python3 main.py --seasons 5           # 5 seasons, drivers move teams between them
python3 main.py --seasons 10 --quiet  # only standings + transfer news each year
python3 main.py --seed 42             # reproducible results
python3 main.py --randomize           # force a fresh random result
python3 main.py --start-year 2026 --seasons 3
python3 main.py --round 16 --seed 42 # simulate only Round 16 (Italy)
```

No dependencies beyond the Python standard library.

## Project layout

```
main.py              CLI entry point — parses args, runs the season loop
f1sim/
  models.py           Driver, Team, Track dataclasses + rating definitions
  data.py              2026 starting grid and 24-round calendar
  simulation.py        Practice / qualifying / race math, points table
  season.py            Runs a calendar of weekends, tracks/prints standings
  transfers.py          Off-season contract expiry, sackings, signings, rookies
```

## How the sim works

- **Ratings (0-100):** each driver has `pace`, `racecraft`, `consistency`,
  `wet_skill`, `experience`, `aggression`. Each team has `car_performance`,
  `reliability`, `pit_crew`. These are subjective flavour numbers, not
  official ratings — tune them freely in `data.py`. Current-season SPS/TMS
  references from the driver data source add a bounded form adjustment, so a
  driver in strong real-world form can outperform their static rating.
- **Qualifying:** Q1 (22 → 15), Q2 (15 → 10), Q3 (top 10 for pole), each
  session re-rolling a performance score (car-weighted, plus driver skill
  and Gaussian noise). Wet-weekend rolls re-weight toward `wet_skill`.
- **Race:** each grid slot gets a performance score (pace + racecraft +
  a grid-position advantage that's bigger at hard-to-overtake tracks like
  Monaco) plus a DNF roll driven by team reliability and driver
  aggression-vs-consistency. Standard 25-18-15-...-1 points; fastest lap is
  displayed but awards no championship bonus.
- **Transfers (`transfers.py`, runs between seasons):** drivers age a year;
  core ratings rise through age 25, hold steady through 34, decline from 35,
  and decline faster from 38. Strong results versus a teammate add a rating
  point, while a clearly weaker season loses one. Contracts count down each
  year; out-of-contract drivers become free agents; a driver who badly
  underperforms a teammate can be dropped early; retirement risk starts at
  age 35 and drivers cannot continue beyond age 45. Free agents are matched
  to open seats by overall skill vs. team tier (front-running teams get first
  pick); any seats still open go to a freshly generated rookie. F2 and F3
  prospect profiles age and follow the same age-based rating curve every year;
  drivers aged 45 or older cannot be promoted to a first F1 seat. Generated
  rookies follow the same curve after their first F1 season.

## Easy ways to extend it

- **Sprint weekends:** add an `is_sprint` branch in `season.run_weekend`
  that calls a short sprint-quali + sprint-race before the main event and
  awards sprint points (8-7-6-5-4-3-2-1).
- **Weather/strategy detail:** dry races choose from varied one-stop and
  occasional two-stop plans such as M-H, H-M, S-H, and S-M-S. Tyre wear,
  pit-lane loss, pit-crew speed, driver style, and random strategy calls all
  influence the choice; wet races use intermediates in the current model.
- **Persistence:** `Team`/`Driver` are plain dataclasses — trivial to
  `dataclasses.asdict()` and dump to JSON if you want to save/load a
  franchise across runs instead of always starting from 2026.
- **Interactive control:** swap `transfers.run_offseason`'s auto-matching
  for prompts so *you* pick which free agent signs where, or which of your
  team's two drivers to keep.
# f1_project
