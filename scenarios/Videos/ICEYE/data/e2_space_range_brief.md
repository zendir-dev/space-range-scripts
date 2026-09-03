# Space Range 5-v-1 compressed plane-change exercise

**Start the scenario at `2026-05-14T00:00:00Z` (UTC).**

At this epoch ICEYE-X36 is already near 97.84° inclination. The five Cosmos spacecraft are near 96.96°. This exercise preserves their 11 catalog-derived inclination steps and ΔV magnitudes, but compresses the historical 14–21 May fleet sequence into consecutive node opportunities ending at **T+03:33:13**. This is an inclination match, not a claim that the full orbital planes coincide.

## Initial orbits

| Spacecraft | NORAD | Role | Spaceflux optics? | Inclination | Semi-major axis | Burns | Total ΔV |
|---|---:|---|---|---:|---:|---:|---:|
| ICEYE-X36 | 59103 | Chief | No — catalog only | 97.838° | 6912.4 km | 0 | — |
| COSMOS 2610 | 68758 | Deputy | Yes | 96.958° | 6930.1 km | 2 | 111.2 m/s |
| COSMOS 2611 | 68759 | Deputy | No — catalog only | 96.951° | 6932.5 km | 2 | 112.8 m/s |
| COSMOS 2612 | 68762 | Deputy | Yes | 96.964° | 6917.6 km | 2 | 117.3 m/s |
| COSMOS 2613 | 68763 | Deputy | Yes | 96.965° | 6910.1 km | 3 | 107.9 m/s |
| COSMOS 2614 | 68764 | Deputy | Yes | 96.960° | 6909.5 km | 2 | 108.3 m/s |

Each initial-condition record has the shared scenario epoch and its own source TLE epoch. Use `e2_range_initial_conditions.csv` for the full classical elements (radians) or Cartesian TEME state.

## How the plane change is represented

The selected Cosmos catalog gaps all show **positive inclination steps**, from about 96.96° toward ICEYE-X36 near 97.84°. A plane change rotates the velocity vector out of the current orbital plane; it is not primarily an altitude-raising burn.

Directions use each Cosmos spacecraft's instantaneous **RTN local orbital frame**: R is radial outward, +N is `r × v` (angular momentum), and T = N × R is transverse/prograde. N is perpendicular to the plane. These are pure cross-track burns: R = 0 and T = 0. To increase inclination, command **+N at an ascending node** or **−N at a descending node**.

## Compressed exercise burn schedule

| Exercise time | UTC at node | Spacecraft | Burn direction | Δi | ΔV | Note |
|---|---|---|---|---:|---:|---|
| T+00:25:31 | 2026-05-14T00:25:31.384735Z | COSMOS 2613 | -N at descending node | 0.336° | 44.5 m/s | inclination step |
| T+00:42:59 | 2026-05-14T00:42:58.799286Z | COSMOS 2610 | -N at descending node | 0.768° | 101.8 m/s | inclination step |
| T+01:13:24 | 2026-05-14T01:13:24.109497Z | COSMOS 2613 | +N at ascending node | 0.414° | 55.0 m/s | mean-motion fit flagged |
| T+01:20:58 | 2026-05-14T01:20:58.476106Z | COSMOS 2612 | +N at ascending node | 0.290° | 38.4 m/s | inclination step |
| T+01:30:54 | 2026-05-14T01:30:53.527223Z | COSMOS 2610 | +N at ascending node | 0.071° | 9.4 m/s | inclination step |
| T+02:01:07 | 2026-05-14T02:01:06.796418Z | COSMOS 2613 | -N at descending node | 0.064° | 8.5 m/s | mean-motion fit flagged |
| T+02:08:42 | 2026-05-14T02:08:41.592408Z | COSMOS 2612 | -N at descending node | 0.597° | 78.9 m/s | inclination step |
| T+02:21:48 | 2026-05-14T02:21:48.374177Z | COSMOS 2611 | -N at descending node | 0.332° | 44.0 m/s | inclination step |
| T+02:45:30 | 2026-05-14T02:45:30.480194Z | COSMOS 2614 | +N at ascending node | 0.335° | 44.5 m/s | mean-motion fit flagged |
| T+03:09:43 | 2026-05-14T03:09:43.024293Z | COSMOS 2611 | +N at ascending node | 0.519° | 68.8 m/s | inclination step |
| T+03:33:13 | 2026-05-14T03:33:12.969361Z | COSMOS 2614 | -N at descending node | 0.482° | 63.8 m/s | mean-motion fit flagged |

Use `e2_range_burns.csv` as Harrison's primary schedule. `e2_range_burns_catalog_timing.csv` preserves the earlier catalog-gap timing reference.

## Read this before loading

- **Frame:** TEME, not J2000/GCRF. Convert before an engine that requires J2000.
- **Burn timing:** intentionally compressed for a short exercise. Each spacecraft retains its source burn order and uses consecutive equatorial nodes after a staggered first burn.
- **Preserved:** all 11 selected Δi steps, ΔV magnitudes, RTN signs, and source catalog windows.
- **Changed:** historical inter-burn and inter-spacecraft waits. Do not present the exercise UTC values as measured Russian burn times.
- **Interpretation:** impulses reproduce catalog inclination steps; they are not reconstructed Russian burns. The catalog also contains RAAN and mean-motion changes, but those are not fitted because natural precession, sparse publication, manoeuvres, and occasional dirty GP fits are entangled.
- **Evidence:** Spaceflux supplied optical angles for Cosmos 2610/2612/2613/2614 only. ICEYE-X36 and Cosmos 2611 are catalog-only.

## Files

- `e2_range_initial_conditions.csv` — practical IC handoff.
- `e2_range_burns.csv` — primary compressed exercise schedule.
- `e2_range_burns_catalog_timing.csv` — uncompressed timing reference.
- `e2_range_ics.json` — complete machine-readable provenance.

Source: stored May 2026 Space-Track GP history. No live API call was made.
