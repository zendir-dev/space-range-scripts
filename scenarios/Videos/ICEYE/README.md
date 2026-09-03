# Reading Intent in Orbit

A Space Range filming kit for a short video about **ICEYE-X36** and five nearby Cosmos spacecraft.

ICEYE-X36 is a commercial SAR satellite on a routine imaging mission. Five recently launched Cosmos spacecraft sit in a nearby but different plane. Over a span of days they make a series of inclination changes toward ICEYE's orbit — individually ambiguous, collectively a coordinated commitment. Once the planes match, proximity becomes possible: inspection, shadowing, and the ability to approach again at will. Blue cannot outrun five vehicles that have already spent that much ΔV, so the response is custody: extra sensors, better ranging, and a clearer picture of when the pattern first became actionable.

The video is about that decision window — noticing the pattern early enough to still do something about it.

Load each stage from `config/` and film it separately. Notes, source data, and generated charts live alongside.

## Layout

```
ICEYE/
  README.md
  config/          Studio scenario JSON (section_1 … section_5)
  data/            Source orbits, burns, and provenance
  notes/
    filming.md     Camera, Operator, and take setup
    narrative.md   Spoken script and shot list
  scripts/
    generate_scenarios.py
    make_chart.py
    check_timing.py  Verifies each shot owns one narration beat that fits
  videos/          Generated frames and media (gitignored)
                   media/2-chart.mp4, media/3-chart.mp4
```

## Generate

From the repository root:

```powershell
python "scenarios/Videos/ICEYE/scripts/generate_scenarios.py"
python "scenarios/Videos/ICEYE/scripts/make_chart.py"
```
