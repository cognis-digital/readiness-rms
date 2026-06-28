# readiness-rms — Unit-readiness C-rating

[![CI](https://github.com/cognis-digital/readiness-rms/workflows/CI/badge.svg)](https://github.com/cognis-digital/readiness-rms/actions)
[![Classification](https://img.shields.io/badge/classification-UNCLASSIFIED-green.svg)](./UPSTREAM.md)

> Compute C1/C2/C3/C4 from public AR 220-1 / OPNAVINST 3501.226 doctrine. JSON in, finding-graded report out.


<!-- cognis:example:start -->
## 🔎 Example output

Real, reproducible output from the tool — runs offline:

```console
$ readiness-rms-emit --version
readiness-rms 0.1.0
```

```console
$ readiness-rms-emit --help
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
  --out OUT             Write output to file
  --fail-on {very_high,high,moderate,low,none}
  --classification CLASSIFICATION
                        Operator-supplied banner. PLACEHOLDER. Tool does not
                        interpret.
  -v, --version         show program's version number and exit
```

> Blocks above are real `readiness-rms` output — reproduce them from a clone.

**Sample result format** _(illustrative values — run on your own data for real findings):_

```
{
"readiness_rms": {
"platform": "stix",
"findings": [
{
"id": "1234567890",
"name": "Example Finding 1",
"description": "This is an example finding.",
"created_at": "2023-02-20T14:30:00Z"
},
{
"id": "2345678901",
"name": "Example Finding 2",
"description": "This is another example finding.",
"created_at": "2023-02-21T10:45:00Z"
}
]
}
}
```

<!-- cognis:example:end -->

## Usage — step by step

`readiness-rms` computes unit readiness C-ratings (C1–C4) from public DoD-style inputs and reports any sub-readiness units as findings.

1. **Install:**

   ```bash
   pip install cognis-readiness-rms      # or: pip install -e .
   readiness-rms --version
   ```

2. **Run a scan** over your unit-data directory (`target` defaults to `.`):

   ```bash
   readiness-rms ./units --format console
   ```

3. **Emit JSON** and write it out (formats: `console`, `json`, `markdown`, `sarif`, `oscal`):

   ```bash
   readiness-rms ./units --format json --out readiness.json
   ```

4. **Read the result** — C4 units surface as `RR-C4-<unit>` (very high), C3 as `RR-C3-<unit>` (high), and ready units as `RR-OK-<unit>`:

   ```bash
   jq '.findings[] | {id, severity, message}' readiness.json
   ```

5. **Gate it in CI** — fail when any C4 (not-ready) unit appears:

   ```bash
   readiness-rms ./units --format sarif --out readiness.sarif --fail-on very_high
   ```

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

## Interoperability

`readiness-rms` composes with the 300+ tool Cognis suite — JSON in/out and a shared
OpenAI-compatible `/v1` backbone. See **[INTEROP.md](INTEROP.md)** for the
suite map, composition patterns, and reference stacks.

## Integrations

Forward `readiness-rms`'s findings to STIX/MISP/Sigma/Splunk/Elastic/Slack/webhooks via
[`cognis-connect`](https://github.com/cognis-digital/cognis-connect). See **[INTEGRATIONS.md](INTEGRATIONS.md)**.
