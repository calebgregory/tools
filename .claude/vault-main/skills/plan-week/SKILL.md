---
name: plan-week
description: Plan the week by selecting tasks to focus on. Use when the user wants to decide what to work on this week.
disable-model-invocation: true
---

# Plan Week

Help Caleb pick 5-7 tasks to focus on this week.

## Steps

1. Read `todo/todo.md`
2. Identify candidates — prioritize by:
   - Tasks already tagged `{due:this week}` or with a due date this week
   - Quick wins (small, concrete tasks)
   - Tasks that have been open a long time
   - Spread across life areas so no area is neglected
3. Present a shortlist of ~10 candidates grouped by area, each as a numbered line
4. Ask Caleb to pick 5-7 (or adjust the list)
5. Once confirmed, tag the selected tasks with `{due:this week}` in `todo/todo.md`
6. Remove `{due:this week}` from any tasks that had it previously but weren't selected (they revert to their natural timeframe)

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
