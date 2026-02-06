#!/usr/bin/env python3
"""
Outputs relative dates for use by Claude skills.

Keys are named to match natural phrases ("end of week", "monday", etc.)
so skills can use them directly without mapping tables.
"""
import typing as ty
from dataclasses import dataclass, field, fields
from datetime import date, timedelta

# Friday = start of weekend. Work week is Mon-Thu.
WEEKEND_START = 4  # 0=Mon ... 6=Sun


def _meta(desc: str) -> ty.Any:
    return field(metadata={"desc": desc})


@dataclass(frozen=True)
class RelativeDates:
    # Core
    today: date = _meta("Current date")
    weekday: int = _meta("Day of week (0=Mon, 4=Fri, 5=Sat, 6=Sun)")
    tomorrow: date = _meta("Tomorrow's date")

    # Week boundaries
    week_start: date = _meta("Monday of current week")

    # Workday navigation (work week = Mon-Thu; skips Fri-Sun)
    prev_workday: date = _meta("Previous workday (Thu if today is Mon)")
    next_workday: date = _meta("Next workday (Mon if today is Thu)")
    end_of_workweek: date = _meta("Thursday of current week (last workday)")

    # Named days — "upcoming X" (today if today is X, else next occurrence)
    monday: date = _meta("Upcoming Monday")
    tuesday: date = _meta("Upcoming Tuesday")
    wednesday: date = _meta("Upcoming Wednesday")
    thursday: date = _meta("Upcoming Thursday")
    friday: date = _meta("Upcoming Friday")
    saturday: date = _meta("Upcoming Saturday")
    sunday: date = _meta("Upcoming Sunday")

    # Weekend
    this_weekend: date = _meta("Upcoming Friday (start of weekend)")
    next_weekend: date = _meta("Friday of next week")

    # Calendar boundaries
    end_of_week: date = _meta("Upcoming Sunday (calendar week end)")
    end_of_month: date = _meta("Last day of current month")

    # Explicit "next X"
    next_monday: date = _meta("Monday of next week (always 7+ days from week_start)")


def _derive_relative_dates(today: date) -> RelativeDates:
    wd = today.weekday()
    week_start = today - timedelta(days=wd)

    def _upcoming(target_wd: int) -> date:
        days_ahead = (target_wd - wd) % 7
        return today + timedelta(days=days_ahead)

    monday = _upcoming(0)
    tuesday = _upcoming(1)
    wednesday = _upcoming(2)
    thursday = _upcoming(3)
    friday = _upcoming(4)
    saturday = _upcoming(5)
    sunday = _upcoming(6)

    # end_of_workweek: Thursday of current week (day before WEEKEND_START)
    eow_day = WEEKEND_START - 1  # 3 = Thursday
    end_of_workweek = week_start + timedelta(days=eow_day)

    # prev_workday: skip Fri-Sun backwards
    if wd == 0:  # Monday → previous Thursday
        prev_workday = today - timedelta(days=4)
    elif wd <= 3:  # Tue-Thu → previous day
        prev_workday = today - timedelta(days=1)
    else:  # Fri-Sun → Thursday
        prev_workday = week_start + timedelta(days=3)

    # next_workday: skip Fri-Sun forwards
    if wd < 3:  # Mon-Wed → next day
        next_workday = today + timedelta(days=1)
    elif wd == 3:  # Thursday → next Monday
        next_workday = today + timedelta(days=4)
    else:  # Fri-Sun → next Monday
        next_workday = week_start + timedelta(days=7)

    # this_weekend: upcoming Friday
    this_weekend = friday

    # next_weekend: Friday of next week
    next_weekend = week_start + timedelta(days=7 + WEEKEND_START)

    # end_of_week: upcoming Sunday (calendar week end)
    end_of_week = sunday

    return RelativeDates(
        today=today,
        weekday=wd,
        tomorrow=today + timedelta(days=1),
        week_start=week_start,
        prev_workday=prev_workday,
        next_workday=next_workday,
        end_of_workweek=end_of_workweek,
        monday=monday,
        tuesday=tuesday,
        wednesday=wednesday,
        thursday=thursday,
        friday=friday,
        saturday=saturday,
        sunday=sunday,
        this_weekend=this_weekend,
        next_weekend=next_weekend,
        end_of_week=end_of_week,
        end_of_month=(today.replace(day=28) + timedelta(days=4)).replace(day=1)
        - timedelta(days=1),
        next_monday=week_start + timedelta(days=7),
    )


def _cli() -> None:
    dates = _derive_relative_dates(date.today())
    for f in fields(dates):
        desc = f.metadata.get("desc", "")
        val = getattr(dates, f.name)
        print(f"{f.name}={val}  # {desc}" if desc else f"{f.name}={val}")


if __name__ == "__main__":
    _cli()
