# Project rules

This a small indie game demo using GDScript and Godot.

## Read requirements before any work

Before planning, research, implementation, tests, or review, read both:

- `docs/requirements/functional.md`
- `docs/requirements/non-functional.md`

Re-read affected requirements when they change.

## Keep the implementation simple

Use KISS. Prefer direct code and existing Godot features. GDScript is the main language; follow the project coding style.

Avoid speculative abstractions, unnecessary layers, and deep inheritance. A little duplication can be preferable over premature generalization. Ordinary helper functions, scenes, and built-in Godot types do not require a separate justification.

## PRs and human QA

Agents have standing authorization to push feature branches to this project's `origin` (`https://github.com/VHonzik/ServerFirst.git`) and to create or update PRs, including draft PRs. Do not ask for confirmation for these actions.

Agents must never merge PRs into `main`, enable auto-merge into `main`, or push directly to `main`. These actions are reserved for owner.

Use `.github/pull_request_template.md` for: