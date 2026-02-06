---
name: plan-week
description: Plan the week by selecting tasks to focus on. Use when the user wants to decide what to work on this week.
disable-model-invocation: true
---

# Plan Week

Help Caleb pick 5-7 tasks to focus on this week.

## Steps

1. Run `~/tools/relative_dates.py` to get `week_start` and `end_of_workweek`
2. Read `todo/todo.md`
3. Identify candidates — prioritize by:
   - Tasks with `{due:YYYY-MM-DD}` where date falls in `[week_start, week_start+6]`
   - Quick wins (small, concrete tasks)
   - Tasks that have been open a long time
   - Spread across life areas so no area is neglected
4. Present a shortlist of ~10 candidates grouped by area, each as a numbered line
5. Ask Caleb to pick 5-7 (or adjust the list)
6. Once confirmed, tag selected tasks with `{due:YYYY-MM-DD}` using Thursday's date (`end_of_workweek`) if they don't already have a date this week
7. Unselected tasks that had a due date matching this week's Thursday: remove `{due:...}` tag (they revert to their natural timeframe)

## Output format

```
### Candidates

**home**
1. towel rack
2. buy spare tire for Angelo

**art**
3. renew Bitwig upgrade plan

**community**
4. ...

**admin**
5. ...

Pick 5-7 numbers (or tell me to adjust):
```
