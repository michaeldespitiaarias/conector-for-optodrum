# OptoDrum Connector sample data

One bundled demo project, light enough to read in one sitting, real
enough to exercise the whole pipeline.

| Animal | Genotype | Group | ACUITY session | CONTRAST session (0.011 c/deg) |
|---|---|---|---|---|
| M001 | WT | Control | `cycle="0.52"` | `contrast="32.5"` |
| M002 | WT | Control | `cycle="0.47"` | `contrast="-1"` (below detection threshold) |

M002's own CONTRAST session deliberately hits the `contrast == -1`
reading (below the detection threshold), so opening this project and
pressing Run demonstrates `process_optodrum`'s own `-1 → 99.99` rule
directly in the output, not just in the test suite.

## Structure

```
samples/
├── data/Demo Project/
│   ├── 2025_mouse_M001_optomotor_visualacuity/trial1.summary
│   ├── 2025_mouse_M001_optomotor_0.011/trial1.summary
│   ├── 2025_mouse_M002_optomotor_visualacuity/trial1.summary
│   ├── 2025_mouse_M002_optomotor_0.011/trial1.summary
│   └── _metadata.csv
├── output/Demo Project/
│   └── optodrum_report.csv      # already generated, one row per animal
└── _fabricate_samples.py        # regenerates both folders from scratch
```

## Trying it in the app

On Home, set **Data folder** to `samples/data/Demo Project`, pick any
**Output folder**, and Run. `optodrum_report.csv` should match
`samples/output/Demo Project/optodrum_report.csv` exactly.

## Regenerating

```bash
cd "conector-for-optodrum"
python3 samples/_fabricate_samples.py
```

Idempotent: deletes and rebuilds both `data/Demo Project/` and
`output/Demo Project/` from the script's own literal values every time.
