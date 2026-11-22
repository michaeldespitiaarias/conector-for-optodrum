# OptoDrum Connector test suite

The suite covers the engines, the statistical modules, the reports and,
without a visible window, the graphical interface.

```bash
pytest                         # complete suite, from the repository root
pytest tests/test_optodrum.py -v      # one file
```

## Conventions

- `conftest.py` adds the source folders to the import path and
  provides a random generator with seed 42.
- `VISOLAB_SETTINGS_DIR` points to a temporary folder, so that no test
  reads or modifies the user's settings or recent analyses.
- Tests build their inputs in `tmp_path`; `samples/output/` is
  read-only reference data used by the integration tests.
- Deprecation, user, runtime and future warnings are ignored globally;
  a test that asserts a warning enables it locally.
- The graphical tests are skipped when tkinter has no display.

## Files

| File | Content |
|---|---|
| `test_gui_smoke.py` | Headless construction of the interface (skipped without a display) |
| `test_i18n.py` | Every interface string has a Spanish entry, and no page shows English text in Spanish |
| `test_optodrum.py` | Parsing of `.summary` files, folder names and threshold rules |
| `test_packaging.py` | Every module loaded by name at run time is declared in the standalone build |
| `test_samples.py` | Agreement with the bundled example output |
