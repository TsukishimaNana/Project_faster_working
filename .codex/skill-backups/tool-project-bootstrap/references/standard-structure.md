# Standard Tool Project Structure

Use this as the default shape for a personal workflow tool project:

```text
tools/<tool-name>/
  README.md
  Handoff.md
  agents.md
  pyproject.toml              # if Python is used
  package.json                # if Node/OpenSpec tooling is used
  src/<package_name>/         # source code
  tests/                      # automated tests
  openspec/                   # OpenSpec project and changes
  docs/                       # supplemental docs and decisions
  examples/input/             # reproducible non-original sample inputs
  examples/output/            # generated output and debug artifacts
  knowledge_base/             # project knowledge/reference material
  assets/                     # fonts/templates/static assets
```

Adjust for the tool, but preserve these ideas:

- Keep original/reference files separate from generated outputs.
- Keep `Handoff.md` and `agents.md` at the project root.
- Keep generated output outside read-only source directories.
- Record validation commands where future agents can find them.
