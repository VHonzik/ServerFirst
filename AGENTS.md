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

## Commit messages

Use this format:

```text
<type>(<scope>): <description>

[optional body]

AI-Models: <short model name(s)>
Signed-off-by: <name> <email>
```

- Use only these lowercase types:
  - `feat`: new functionality.
  - `fix`: bug fixes.
  - `docs`: documentation-only changes.
  - `chore`: maintenance, tooling, dependencies, tests, or refactoring that does not add functionality or fix a bug.
- Always include a nonempty scope naming the affected component or area, such as `combat`, `ui`, or `build`.
- Follow the scope with a colon and one space.
- Keep the entire subject line at most 50 characters, including the prefix. Use a concise, imperative description without a trailing period.
- Include a body only when useful to explain the change or its rationale. Separate it from the subject with a blank line and wrap lines at 72 characters.
- Do not use `!`, `BREAKING CHANGE`, or `BREAKING-CHANGE` syntax.
- End every commit message with exactly these footer types, in this order:
  1. `AI-Models:` listing the short, accurate names of the models that contributed to the changes, separated by commas.
  2. `Signed-off-by:` containing the committer’s configured Git name and email. Add this using `git commit --signoff`.
- Before writing `AI-Models:`, attempt to resolve each contributing model's specific name and reasoning effort from session metadata. Include verified effort in parentheses, for example `GPT-6.1 Sol (high)`; omit details that cannot be verified rather than guessing.
- Separate the footer block from the preceding text with a blank line. Do not include any other footers or trailers.
- Never invent model names or sign-off identities.

## PRs and human QA

Agents have standing authorization to push feature branches to this project's `origin` (`https://github.com/VHonzik/ServerFirst.git`) and to create or update PRs, including draft PRs. Do not ask for confirmation for these actions.

Agents must never merge PRs into `main`, enable auto-merge into `main`, or push directly to `main`. These actions are reserved for owner.

Use `.github/pull_request_template.md` for:
