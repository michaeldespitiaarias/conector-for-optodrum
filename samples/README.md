# OptoDrum Connector example project

One example project with two animals and both staircase types:

| Animal | Genotype | Group | ACUITY session | CONTRAST session (0.011 c/deg) |
|---|---|---|---|---|
| M001 | WT | Control | `cycle="0.52"` | `contrast="32.5"` |
| M002 | WT | Control | `cycle="0.47"` | `contrast="-1"` (below the detection threshold) |

The CONTRAST session of M002 contains the value −1, which is written as
99.99 in `optodrum_report.csv`.

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
│   └── optodrum_report.csv      one row per animal
└── _fabricate_samples.py        rebuilds both folders
```

A run with `samples/data/Demo Project` as Data folder produces an
`optodrum_report.csv` identical to
`samples/output/Demo Project/optodrum_report.csv`.

## Regeneration

```bash
python samples/_fabricate_samples.py
```

The script deletes and rewrites `data/Demo Project/` and
`output/Demo Project/` from the values it contains.
