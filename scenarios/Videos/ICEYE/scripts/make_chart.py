"""Render the Section 2 inclination-versus-date chart as a PNG frame sequence.

Section 2 shows a frozen 16 May snapshot, so the simulator cannot depict the
eight-day inclination campaign that the narration describes. This chart is the
only representation in the video that renders time, and it plots the catalogue
timing reference directly.

    python "scenarios/Videos/ICEYE/scripts/make_chart.py"            # Section 2, stops 16 May
    python "scenarios/Videos/ICEYE/scripts/make_chart.py" --full      # Section 3, 16 -> 21 May

The Section 3 variant resumes at the 16 May stop so its first frame matches the
Section 2 variant's last frame and the two cut together without a rewind.

Import the output folder into the editor as an image sequence at 20 fps.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.dates as mdates
import matplotlib.pyplot as plt

ICEYE_DIR = Path(__file__).resolve().parent.parent
VIDEOS_DIR = ICEYE_DIR / "videos"
MEDIA_DIR = VIDEOS_DIR / "media"

FPS = 20
WIDTH_PX, HEIGHT_PX = 1920, 1080
DPI = 100

# ICEYE-X36 never manoeuvres; it is the destination plane the campaign converges on.
ICEYE_INCLINATION = 97.837601

# Source: data/e2_range_initial_conditions.csv, TEME elements at 2026-05-14T00:00:00Z.
INITIAL = {
    "COSMOS 2613": 96.965236,
    "COSMOS 2610": 96.957546,
    "COSMOS 2612": 96.964342,
    "COSMOS 2611": 96.950662,
    "COSMOS 2614": 96.960126,
}

# Source: data/e2_range_burns_catalog_timing.csv, using the uncompressed catalogue
# node times rather than the compressed exercise schedule. These are the real dates
# the section's chronology depends on.
STEPS = [
    ("2026-05-14T04:24", "COSMOS 2613", 0.3362),
    ("2026-05-14T11:34", "COSMOS 2613", 0.4145),
    ("2026-05-14T23:31", "COSMOS 2613", 0.0640),
    ("2026-05-15T08:36", "COSMOS 2610", 0.7678),
    ("2026-05-15T22:46", "COSMOS 2612", 0.2897),
    ("2026-05-15T23:44", "COSMOS 2610", 0.0711),
    ("2026-05-16T10:43", "COSMOS 2612", 0.5968),
    ("2026-05-20T05:03", "COSMOS 2611", 0.3316),
    ("2026-05-20T16:13", "COSMOS 2611", 0.5194),
    ("2026-05-21T02:48", "COSMOS 2614", 0.3355),
    ("2026-05-21T14:46", "COSMOS 2614", 0.4820),
]

# Each craft keeps one colour in both variants so the Section 2 and Section 3 charts
# cut together. Craft that have not moved yet are dimmed by alpha rather than by
# colour, which is what produces the "three of five" read at the 16 May stop.
COLOURS = {
    "COSMOS 2613": "#FB923C",
    "COSMOS 2610": "#F87171",
    "COSMOS 2612": "#FBBF24",
    "COSMOS 2611": "#A78BFA",
    "COSMOS 2614": "#34D399",
}

BACKGROUND = "#0B0F1A"
PANEL = "#111827"
GRID = "#1E2638"
TEXT = "#E5E7EB"
MUTED = "#6B7280"
ICEYE_COLOUR = "#22D3EE"

AXIS_START = datetime(2026, 5, 14, 0, 0)
AXIS_END = datetime(2026, 5, 21, 23, 59)
SECTION_2_STOP = datetime(2026, 5, 16, 12, 0)

HOLD_IN_S = 2.0
SWEEP_S = 8.0
HOLD_OUT_S = 3.0


def parse_steps() -> list[tuple[datetime, str, float]]:
    return [
        (datetime.fromisoformat(stamp), craft, delta) for stamp, craft, delta in STEPS
    ]


def series_until(steps, moment: datetime):
    """Step-function points per craft, truncated at `moment`."""
    current = dict(INITIAL)
    points = {name: [(AXIS_START, value)] for name, value in INITIAL.items()}
    completed = 0
    remaining = {name: 0 for name in INITIAL}
    for _, craft, _ in steps:
        remaining[craft] += 1

    done = {name: 0 for name in INITIAL}
    for when, craft, delta in steps:
        if when > moment:
            break
        current[craft] += delta
        points[craft].append((when, current[craft]))
        done[craft] += 1
        if done[craft] == remaining[craft]:
            completed += 1

    for name in points:
        points[name].append((moment, current[name]))
    return points, completed


def render(moment: datetime, stop: datetime, path: Path, steps) -> None:
    fig = plt.figure(figsize=(WIDTH_PX / DPI, HEIGHT_PX / DPI), dpi=DPI)
    fig.patch.set_facecolor(BACKGROUND)
    ax = fig.add_axes([0.08, 0.12, 0.78, 0.78])
    ax.set_facecolor(PANEL)

    for spine in ax.spines.values():
        spine.set_color(GRID)
    ax.grid(True, color=GRID, linewidth=0.8, alpha=0.7)
    ax.set_axisbelow(True)

    ax.set_xlim(AXIS_START, AXIS_END)
    ax.set_ylim(96.9, 98.0)
    ax.xaxis.set_major_locator(mdates.DayLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
    ax.tick_params(colors=TEXT, labelsize=15)
    ax.set_ylabel("Inclination  (degrees)", color=TEXT, fontsize=17, labelpad=14)

    # Everything to the right of the playhead is unrevealed. In Section 2 this is
    # where 2611 and 2614 still have their 20-21 May steps hiding.
    ax.axvspan(moment, AXIS_END, color=BACKGROUND, alpha=0.55, zorder=1)

    ax.axhline(
        ICEYE_INCLINATION, color=ICEYE_COLOUR, linewidth=2.6, zorder=3, alpha=0.95
    )
    # Sits below the line: completed-craft labels are pushed upward and would
    # otherwise collide with this once three of them converge.
    ax.text(
        AXIS_START + timedelta(hours=3),
        ICEYE_INCLINATION - 0.035,
        "ICEYE-X36  97.838°   DESTINATION PLANE",
        color=ICEYE_COLOUR,
        fontsize=15,
        fontweight="bold",
        zorder=6,
    )

    points, completed = series_until(steps, moment)
    moved_labels: list[tuple[float, str]] = []
    unmoved: list[str] = []

    for name, series in points.items():
        xs = [item[0] for item in series]
        ys = [item[1] for item in series]
        moved = ys[-1] > INITIAL[name] + 1e-9
        ax.plot(
            xs,
            ys,
            drawstyle="steps-post",
            color=COLOURS[name],
            linewidth=3.2 if moved else 2.0,
            alpha=1.0 if moved else 0.45,
            zorder=5 if moved else 4,
            solid_capstyle="round",
        )
        ax.scatter(
            [xs[-1]],
            [ys[-1]],
            s=70 if moved else 40,
            color=COLOURS[name],
            alpha=1.0 if moved else 0.5,
            zorder=6,
        )
        if moved:
            moved_labels.append((ys[-1], name))
        else:
            unmoved.append(name)

    # Once the playhead nears the right edge there is no room for labels beside it,
    # so they flip to the left. Section 2 stops at 16 May and never triggers this;
    # the --full sweep to 21 May does.
    span = (AXIS_END - AXIS_START).total_seconds()
    near_right = (moment - AXIS_START).total_seconds() / span > 0.68
    side = -1 if near_right else 1
    align = "right" if near_right else "left"
    label_x = moment + side * timedelta(hours=5)
    text_x = moment + side * timedelta(hours=7)

    # The completed craft land within 0.07 deg of each other, which is far closer
    # than a text row is tall, so labels are pushed apart and given leader lines.
    min_gap = 0.030
    placed_y = None
    for true_y, name in sorted(moved_labels):
        text_y = true_y if placed_y is None else max(true_y, placed_y + min_gap)
        placed_y = text_y
        ax.plot(
            [moment, label_x],
            [true_y, text_y],
            color=COLOURS[name],
            linewidth=1.0,
            alpha=0.45,
            zorder=5,
        )
        ax.text(
            text_x,
            text_y,
            f"{name}  {true_y:.3f}°",
            color=COLOURS[name],
            fontsize=14,
            fontweight="bold",
            va="center",
            ha=align,
            zorder=6,
            # Converged craft sit almost on top of each other, so the step lines
            # would otherwise run straight through the label text.
            bbox=dict(facecolor=PANEL, edgecolor="none", alpha=0.88, pad=2.5),
        )

    # Everything still at its launch inclination collapses into one row, which is
    # also the "three of five" read: a tight bundle up top, the rest untouched.
    if unmoved:
        names = " · ".join(sorted(name.split()[-1] for name in unmoved))
        ax.text(
            text_x,
            min(INITIAL[name] for name in unmoved) - 0.012,
            f"COSMOS {names}   ~96.96°   UNMOVED",
            color=MUTED,
            fontsize=14,
            va="center",
            ha=align,
            zorder=6,
        )

    ax.axvline(moment, color=TEXT, linewidth=1.8, alpha=0.85, zorder=7)
    ax.text(
        moment + side * timedelta(hours=2),
        97.95,
        moment.strftime("%d %b %Y  %H:%M UTC"),
        color=TEXT,
        fontsize=16,
        fontweight="bold",
        va="center",
        ha=align,
        zorder=8,
    )

    fig.text(
        0.08,
        0.945,
        "COSMOS INCLINATION CAMPAIGN",
        color=TEXT,
        fontsize=25,
        fontweight="bold",
    )
    fig.text(
        0.08,
        0.915,
        "Catalogue-derived inclination steps, 14-21 May 2026",
        color=MUTED,
        fontsize=15,
    )
    fig.text(
        0.86,
        0.945,
        f"COMPLETED  {completed} of 5",
        color=ICEYE_COLOUR if completed else MUTED,
        fontsize=21,
        fontweight="bold",
        ha="right",
    )
    fig.text(
        0.08,
        0.045,
        "Source: catalogue gap analysis. Steps bound the changes; they do not measure exact impulses.",
        color=MUTED,
        fontsize=13,
    )

    fig.savefig(path, facecolor=BACKGROUND)
    plt.close(fig)


def encode_video(frame_dir: Path, target: Path, fps: int) -> None:
    """Mux the rendered frames into an MP4.

    Uses OpenCV rather than an ffmpeg binary, since ffmpeg is not installed here.
    The mp4v codec is MPEG-4 Part 2, which every editor reads; it is not as small
    as H.264 but this is a 13 second title card, not delivery footage.
    """
    import cv2

    frames = sorted(frame_dir.glob("frame_*.png"))
    if not frames:
        raise SystemExit(f"No frames found in {frame_dir}")

    first = cv2.imread(str(frames[0]))
    height, width = first.shape[:2]
    writer = cv2.VideoWriter(
        str(target), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height)
    )
    if not writer.isOpened():
        raise SystemExit("Could not open the video writer.")
    try:
        for frame in frames:
            writer.write(cv2.imread(str(frame)))
    finally:
        writer.release()

    size_mb = target.stat().st_size / 1e6
    print(f"Wrote {target} ({size_mb:.1f} MB, {len(frames) / fps:.1f} s at {fps} fps)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--full",
        action="store_true",
        help="Sweep to 21 May for Section 3, resuming from the 16 May stop.",
    )
    parser.add_argument(
        "--from-start",
        action="store_true",
        help="With --full, replay from 14 May instead of resuming from 16 May.",
    )
    parser.add_argument(
        "--no-video",
        action="store_true",
        help="Render the PNG sequence only and skip MP4 encoding.",
    )
    parser.add_argument("--outdir", default=None)
    args = parser.parse_args()

    # Section 3 cuts straight out of Section 2's closing hold, so its first frame has
    # to be Section 2's last frame. Sweeping from 14 May again would read as a rewind.
    stop = AXIS_END if args.full else SECTION_2_STOP
    start = SECTION_2_STOP if (args.full and not args.from_start) else AXIS_START

    outdir = Path(args.outdir) if args.outdir else VIDEOS_DIR / (
        "chart_frames_full" if args.full else "chart_frames"
    )
    outdir.mkdir(parents=True, exist_ok=True)
    for stale in outdir.glob("frame_*.png"):
        stale.unlink()

    steps = parse_steps()
    hold_in = int(HOLD_IN_S * FPS)
    sweep = int(SWEEP_S * FPS)
    hold_out = int(HOLD_OUT_S * FPS)
    span = (stop - start).total_seconds()

    index = 0
    for _ in range(hold_in):
        render(start, stop, outdir / f"frame_{index:04d}.png", steps)
        index += 1
    for step in range(1, sweep + 1):
        moment = start + timedelta(seconds=span * step / sweep)
        render(moment, stop, outdir / f"frame_{index:04d}.png", steps)
        index += 1
    for _ in range(hold_out):
        render(stop, stop, outdir / f"frame_{index:04d}.png", steps)
        index += 1

    print(f"Wrote {index} frames to {outdir}")
    print(f"Import as an image sequence at {FPS} fps ({index / FPS:.1f} s).")

    if not args.no_video:
        MEDIA_DIR.mkdir(parents=True, exist_ok=True)
        name = "3-chart.mp4" if args.full else "2-chart.mp4"
        encode_video(outdir, MEDIA_DIR / name, FPS)


if __name__ == "__main__":
    main()
