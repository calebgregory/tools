#!/usr/bin/env python3
import argparse
import datetime
import typing as ty


def _parse_date(s: str) -> datetime.date:
    return datetime.date.fromisoformat(s)


class LifeStats(ty.NamedTuple):
    birth_date: datetime.date
    projected_death: datetime.date
    total_days: int
    days_alive: int
    days_remaining: int
    percent_lived: float


def calculate(birth_date: datetime.date, expected_age: int, *, today: datetime.date) -> LifeStats:
    projected_death = birth_date.replace(year=birth_date.year + expected_age)
    total_days = (projected_death - birth_date).days
    days_alive = (today - birth_date).days

    return LifeStats(
        birth_date=birth_date,
        projected_death=projected_death,
        total_days=total_days,
        days_alive=days_alive,
        days_remaining=(projected_death - today).days,
        percent_lived=days_alive / total_days * 100,
    )


def _report(stats: LifeStats) -> str:
    bar_width = 40
    filled = round(bar_width * stats.percent_lived / 100)
    bar = "#" * filled + "-" * (bar_width - filled)
    return "\n".join(
        [
            f"Born:           {stats.birth_date}",
            f"Projected end:  {stats.projected_death}",
            f"Days alive:     {stats.days_alive:,}",
            f"Days remaining: {stats.days_remaining:,}",
            f"Total expected: {stats.total_days:,}",
            f"Life lived:     {stats.percent_lived:.2f}%",
            f"[{bar}]",
        ]
    )


def cli() -> None:
    parser = argparse.ArgumentParser(description="How far through life are you?")
    parser.add_argument("birth_date", type=_parse_date, metavar="BIRTH_DATE", help="YYYY-MM-DD")
    parser.add_argument("expected_age", type=int, metavar="EXPECTED_AGE", help="years")
    args = parser.parse_args()
    stats = calculate(args.birth_date, args.expected_age, today=datetime.date.today())
    print(_report(stats))


if __name__ == "__main__":
    cli()
