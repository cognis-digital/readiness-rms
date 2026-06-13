# readiness-rms — Unit-readiness C-rating

[![CI](https://github.com/cognis-digital/readiness-rms/workflows/CI/badge.svg)](https://github.com/cognis-digital/readiness-rms/actions)
[![Classification](https://img.shields.io/badge/classification-UNCLASSIFIED-green.svg)](./UPSTREAM.md)

> Compute C1/C2/C3/C4 from public AR 220-1 / OPNAVINST 3501.226 doctrine. JSON in, finding-graded report out.

<!-- cognis:layman:start -->
## What is this?

readiness-rms is a command-line tool that calculates the official military unit-readiness grade (C1 through C4) for any Army or Navy unit, using publicly documented Department of Defense rules. You give it a simple data file listing a unit's headcount, available equipment, training completion, and inspection results, and it tells you exactly where the unit stands and which specific area is dragging the grade down. It is built for defense analysts, program managers, and IT teams that need to feed readiness data into compliance pipelines or briefings without standing up a full enterprise system.
<!-- cognis:layman:end -->

## Upstream

Forks / wraps **https://github.com/apache/superset**. See [`UPSTREAM.md`](./UPSTREAM.md) for the
licensing posture, supported commits, and how to upgrade.

## What this adds for military / IC use

- Public-doctrine C-rating math
- 6 sub-ratings (personnel fill / deployable / equipment on-hand / mission-capable / training / inspection)
- Worst-of aggregation matches DoD methodology

<!-- cognis:domains:start -->
## Domains

**Primary domain:** Government & Compliance  ·  **JTF MERIDIAN division:** IRONCLAD · ANVIL

**Topics:** `cognis` `compliance` `govtech` `grc`

Part of the **Cognis Neural Suite** — 300+ source-available tools organized across 12 domains under the JTF MERIDIAN command structure. See the [suite on GitHub](https://github.com/cognis-digital) and [jtf-meridian](https://github.com/cognis-digital/jtf-meridian) for how the pieces fit together.
<!-- cognis:domains:end -->

<!-- cognis:install:start -->
## Install

`readiness-rms` is source-available (not published to PyPI) — every method below installs
straight from GitHub. Pick whichever you prefer; the one-line scripts auto-detect
the best tool available on your machine.

**One-liner (Linux / macOS):**
```sh
curl -fsSL https://raw.githubusercontent.com/cognis-digital/readiness-rms/HEAD/install.sh | sh
```

**One-liner (Windows PowerShell):**
```powershell
irm https://raw.githubusercontent.com/cognis-digital/readiness-rms/HEAD/install.ps1 | iex
```

**Or install manually — any one of:**
```sh
pipx install "git+https://github.com/cognis-digital/readiness-rms.git"     # isolated (recommended)
uv tool install "git+https://github.com/cognis-digital/readiness-rms.git"  # uv
pip install "git+https://github.com/cognis-digital/readiness-rms.git"      # pip
```

**From source:**
```sh
git clone https://github.com/cognis-digital/readiness-rms.git
cd readiness-rms && pip install .
```

Then run:
```sh
readiness-rms --help
```
<!-- cognis:install:end -->

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
    pip install "git+https://github.com/cognis-digital/readiness-rms.git"
    readiness-rms . --format=oscal --out=assessment-results.json --fail-on=high
- name: Upload to eMASS/Xacta
  run: cognis-rmf-package import assessment-results.json
```

## Part of the Cognis Digital military / IC ecosystem

12 repos. All MIT/Apache-2.0/GPL-3 (per upstream). Cognis additions are
Apache-2.0 unless stated otherwise.

See [the master index](../../MASTER-INDEX.md).

<a name="verification"></a>
## Verification

[![tests](https://img.shields.io/badge/tests-4%20passing-2ea44f.svg)](AUDIT.md)

Every push is verified end-to-end. Latest audit (2026-06-13):

```text
tests        : 4 passed, 0 failed, 0 errored
compile      : all modules parse
cli          : readiness-rms 0.1.0
package      : readiness_rms
```

<details><summary>CLI surface (<code>--help</code>)</summary>

```text
usage: readiness-rms [-h] [--format {console,json,markdown,sarif,oscal}]
                     [--out OUT]
                     [--fail-on {very_high,high,moderate,low,none}]
                     [--classification CLASSIFICATION] [-v]
                     [target]

readiness-rms — Cognis Digital · Military/IC ecosystem

positional arguments:
  target                Path/target

options:
  -h, --help            show this help message and exit
  --format {console,json,markdown,sarif,oscal}
```
</details>

Full machine-readable results: [`AUDIT.md`](AUDIT.md) · regenerate with `python -m readiness_rms --help` + `pytest -q`.

<div align="right"><a href="#top">↑ back to top</a></div>

