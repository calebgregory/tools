#!/usr/bin/env python3
"""
Outputs workday-relative dates for use by Claude skills.

Keys are named to match natural phrases ("end of week", "monday", etc.)
so skills can use them directly without mapping tables.
"""
import typing as ty
from dataclasses import dataclass, field, fields
from datetime import date, timedelta


def _meta(desc: str) -> ty.Any:
    return field(metadata={"desc": desc})


@dataclass(frozen=True)
class RelativeWorkdates:
    # Core
    today: date = _meta("Current date")
    weekday: int = _meta("Day of week (0=Mon, 4=Fri, 5=Sat, 6=Sun)")
    tomorrow: date = _meta("Tomorrow's date")

    # Week boundaries
    week_start: date = _meta("Monday of current week (for archives)")

    # Workday navigation
    prev_workday: date = _meta("Previous workday (Fri if today is Mon)")
    next_workday: date = _meta("Next workday (Mon if today is Fri)")

    # Due date phrases — "monday" means the upcoming Monday as a deadline
    monday: date = _meta("Upcoming Monday (today if Mon, else next)")
    tuesday: date = _meta("Upcoming Tuesday")
    wednesday: date = _meta("Upcoming Wednesday")
    thursday: date = _meta("Upcoming Thursday")
    friday: date = _meta("Upcoming Friday")
    end_of_week: date = _meta("Upcoming Friday (alias for friday)")
    end_of_month: date = _meta("Last day of current month")

    # Explicit "next X"
    next_monday: date = _meta("Monday of next week (always 7+ days from week_start)")


def _derive_relative_workdates(today: date) -> RelativeWorkdates:
    wd = today.weekday()
    week_start = today - timedelta(days=wd)

    def _upcoming_weekday(target_wd: int) -> date:
        """Return today if today is target_wd, else the next occurrence."""
        days_ahead = (target_wd - wd) % 7
        return today + timedelta(days=days_ahead)

    monday, tuesday, wednesday, thursday = (_upcoming_weekday(x) for x in range(4))

    # Friday: if today is Sat/Sun, return next Friday
    if wd <= 4:
        friday = today + timedelta(days=(4 - wd))
    else:
        friday = today + timedelta(days=(11 - wd))

    return RelativeWorkdates(
        today=today,
        weekday=wd,
        tomorrow=today + timedelta(days=1),
        week_start=week_start,
        prev_workday=today - timedelta(days=(3 if wd == 0 else 1)),
        next_workday=today + timedelta(days=(3 if wd == 4 else 1)),
        monday=monday,
        tuesday=tuesday,
        wednesday=wednesday,
        thursday=thursday,
        friday=friday,
        end_of_week=friday,
        end_of_month=(today.replace(day=28) + timedelta(days=4)).replace(day=1)
        - timedelta(days=1),
        next_monday=week_start + timedelta(days=7),
    )


def _cli() -> None:
    dates = _derive_relative_workdates(date.today())
    for f in fields(dates):
        desc = f.metadata.get("desc", "")
        val = getattr(dates, f.name)
        print(f"{f.name}={val}  # {desc}" if desc else f"{f.name}={val}")


if __name__ == "__main__":
    _cli()
