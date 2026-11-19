# Week 0: model answers and review notes

Code: [about_me.py](about_me.py). Lesson: [LESSON.md](../../exercises/week-0-git-and-setup/LESSON.md).

## Checkpoint answers

**Why do we never push to `main`?**
`main` is the one branch everyone merges from, so anything pushed there by mistake lands in
every trainee's branch the next time they run `git merge origin/main`.

A good answer names the consequence (everyone gets the change), not just the rule.

## What a complete week 0 PR looks like

- **Base** `trainee/<your-name>`, **compare** `trainee/<your-name>-week-0`.
- **Files changed:** only `exercises/week-0-git-and-setup/starter/about_me.py`.
- **Description:** every checkpoint item ticked *and* answered. Paste the last line of
  `make check WEEK=0`, the Luganda greeting from `make live WEEK=0`, and your one sentence
  on why we never push to `main`. A ticked box with no answer counts as not done.
- **"What I built":** describes this week's change (filling in `about_me.py`), not
  something else.

## Things that went wrong in week 0 reviews

1. **Merging your own PR.** GitHub lets you click "Merge", but don't. The trainer reviews
   and merges into your branch; that review *is* the assessment.
2. **Opening a PR into `main`.** GitHub picks `main` as the base by default. Always change
   the base to `trainee/<your-name>` before clicking "Create pull request". If you open one
   by mistake, close it and tell the trainer.
3. **Undoing a mistake with more PRs.** If something goes wrong (a wrong merge, a wrong
   base), stop and ask. A "Revert" PR on top of a self-merge makes the history harder to
   follow, not easier.
