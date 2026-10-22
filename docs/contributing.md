# Development and documentation

## Build this site

```text
python -m pip install -r requirements.txt
python -m sphinx -W --keep-going -b html docs _build/html
```

Sphinx uses the Read the Docs theme. GitHub Actions deploys the generated
static HTML to GitHub Pages at `https://trusst-o-ran.github.io/`. A Read the
Docs configuration is also included for an optional future RTD service build;
the active hosting service is GitHub Pages.

## Maintain the shared laboratory

The canonical bundle is `testbed/virtual` in Task 1. Every task repository and
this documentation repository carry an identical copy. `shared-manifest.json`
records the source repository, bundle version, and SHA-256 of managed files.
Review local differences before synchronizing an updated bundle; preserve
local `sources`, `artifacts`, and `results` directories. Never copy build
caches, raw captures, or credentials into another repository.

Run the configuration checker and the portable tests after updating a copy:

```text
python -m pip install -r testbed/virtual/requirements-dev.txt
python testbed/virtual/scripts/testbed.py check
python -m pytest testbed/virtual/tests -q
```

The virtual-testbed workflow checks configuration contracts and software only.
Live builds and smoke tests require the documented Linux runtime. Task-specific
experiment tooling stays in its task repository. Update the task and validation
pages when measured evidence changes; retain the distinction between complete,
inconclusive, infrastructure-failure, and dry-run results.
