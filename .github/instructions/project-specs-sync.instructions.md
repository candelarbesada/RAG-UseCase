---
description: "Use when changing Python source code in this project. Keep the README, project overview, dependency/setup configuration, and project specifications aligned with implemented behavior."
applyTo: "src/**/*.py"
---

# Project specification sync

After changing source code, review the root `README.md` and `docs/PROJECT_OVERVIEW.md` and update them when the change affects documented behavior, architecture, requirements, setup, or limitations. Keep descriptions factual; do not describe roadmap items as implemented.

Also inspect the relevant project configuration and setup files (`pyproject.toml`, `config/requirements.txt`, and `config/setup_env.ps1`). Update configuration when the code change requires different dependencies, runtime settings, or setup steps. Keep dependency declarations aligned; do not make unrelated or no-op configuration edits.

If the change affects test or run instructions, update those instructions and add or adjust focused tests where appropriate. Before finishing, check that documentation links and commands still match the repository.
