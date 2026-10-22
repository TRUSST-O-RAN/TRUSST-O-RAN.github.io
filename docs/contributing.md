# Development

Task repositories contain code and experiment results. The documentation repo
publishes this site with Sphinx and the Read the Docs theme.

```text
python -m pip install -r requirements.txt
python -m pytest -q
```

For the documentation repo:

```text
python -m sphinx -W --keep-going -b html docs _build/html
```

Keep shared files under `testbed/virtual` identical to their recorded manifest.
Keep full raw runs locally; publish small evidence sets with hashes. A proposed
attack, a working control, and a confirmed finding should be labelled separately.
