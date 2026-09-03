"""Check that every shot in notes/narrative.md owns one narration beat and that the
stated shot durations are long enough to speak it.

Run from anywhere:
    python scenarios/Videos/ICEYE/scripts/check_timing.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

NARRATIVE = Path(__file__).resolve().parent.parent / "notes" / "narrative.md"

# Delivery rate for the voice track. 150 words per minute is an unhurried
# documentary pace; anything faster stops matching the orbital visuals.
WORDS_PER_MINUTE = 150
WORDS_PER_SECOND = WORDS_PER_MINUTE / 60

SHOT_RE = re.compile(
    r"^### Shot (\d+)\s*[—-]\s*(.+?)\n+Use \*\*(\d+)[\u2013-](\d+) seconds\*\*"
    r"(.*?)(?=^### |^## |\Z)",
    re.S | re.M,
)
SECTION_RE = re.compile(r"^# Section (\d)(.*?)(?=^# Section |\Z)", re.S | re.M)
NARRATION_RE = re.compile(r"Narration for this shot[^\n]*\n+((?:> .*\n)+)")


def speaking_seconds(text: str) -> float:
    return len(text.split()) / WORDS_PER_SECOND


def main() -> int:
    report = NARRATIVE.read_text(encoding="utf-8")
    problems: list[str] = []
    total_low = total_high = 0

    for section in SECTION_RE.finditer(report):
        number, body = section.group(1), section.group(2)
        shots = list(SHOT_RE.finditer(body))
        section_low = section_high = 0

        for shot in shots:
            index, name, low, high, tail = shot.groups()
            low, high = int(low), int(high)
            section_low += low
            section_high += high

            narration = NARRATION_RE.search(tail)
            if not narration:
                problems.append(
                    f"Section {number} shot {index} ({name.strip()}) has no narration beat"
                )
                continue

            spoken = " ".join(
                line[2:] for line in narration.group(1).splitlines() if line.startswith("> ")
            )
            needed = speaking_seconds(spoken)
            # A shot must fit the words plus a beat of silence at each end, or the
            # narration will run over the cut.
            if low < needed + 1.5:
                problems.append(
                    f"Section {number} shot {index} ({name.strip()}): {low}s is too short for "
                    f"{len(spoken.split())} words (~{needed:.0f}s of speech)"
                )

        total_low += section_low
        total_high += section_high
        print(
            f"Section {number}: {len(shots)} shots, "
            f"{section_low}-{section_high}s (mid {round((section_low + section_high) / 2)}s)"
        )

    mid = round((total_low + total_high) / 2)
    print(f"\nTotal: {total_low}-{total_high}s (mid {mid // 60}:{mid % 60:02d})")

    if problems:
        print("\nProblems:")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    print("\nEvery shot has a dedicated narration beat that fits its duration.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
