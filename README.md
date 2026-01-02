# readiness-rms — Unit-readiness C-rating

[![CI](https://github.com/cognis-digital/readiness-rms/workflows/CI/badge.svg)](https://github.com/cognis-digital/readiness-rms/actions)
[![Classification](https://img.shields.io/badge/classification-UNCLASSIFIED-green.svg)](./UPSTREAM.md)

> Compute C1/C2/C3/C4 from public AR 220-1 / OPNAVINST 3501.226 doctrine. JSON in, finding-graded report out.

## Upstream

Forks / wraps **https://github.com/apache/superset**. See [`UPSTREAM.md`](./UPSTREAM.md) for the
licensing posture, supported commits, and how to upgrade.

## What this adds for military / IC use

- Public-doctrine C-rating math
- 6 sub-ratings (personnel fill / deployable / equipment on-hand / mission-capable / training / inspection)
- Worst-of aggregation matches DoD methodology

## Install

```bash
# Shared library (only once for the whole ecosystem):
pip install -e ../../shared

# This tool:
pip install -e .
```

## Demo

```bash
readiness-rms demos/
```

Outputs are available in five formats — all respect an operator-supplied
classification banner (passed via `--classification`):

```bash
readiness-rms <target> --format=console     # default
readiness-rms <target> --format=json
readiness-rms <target> --format=sarif       # for code-scanning pipelines
readiness-rms <target> --format=markdown    # for PRs / briefings
readiness-rms <target> --format=oscal       # OSCAL Assessment Results skeleton
```

## Classification banner

All output is wrapped with an operator-supplied classification banner.
**Default**: `UNCLASSIFIED//FOR PUBLIC RELEASE`.

> ⚠️ This tool **does not** generate or validate the *content* of higher
> classifications. Operators on cleared systems supply real markings at runtime.
> See [`../shared/cognis_mil/classmark.py`](../../shared/cognis_mil/classmark.py).

## Compliance crosswalks (built in)

Every finding can carry references to:
- **NIST 800-53 Rev 5** controls (e.g. `AC-2(1)`)
- **DISA STIG** rule IDs (e.g. `V-242414`)
- **MITRE ATT&CK** technique IDs (e.g. `T1078`)
- **CCI** (Control Correlation Identifier)

These are emitted in JSON, SARIF, and the OSCAL skeleton.

## CI / RMF integration

```yaml
- name: readiness-rms scan
  run: |
    pip install cognis-readiness-rms
    readiness-rms . --format=oscal --out=assessment-results.json --fail-on=high
- name: Upload to eMASS/Xacta
  run: cognis-rmf-package import assessment-results.json
```

## Part of the Cognis Digital military / IC ecosystem

12 repos. All MIT/Apache-2.0/GPL-3 (per upstream). Cognis additions are
Apache-2.0 unless stated otherwise.

See [the master index](../../MASTER-INDEX.md).
