# linux-lts-silent-fix-oracle

[![CI](https://github.com/Adraca/linux-lts-silent-fix-oracle/actions/workflows/ci.yml/badge.svg)](https://github.com/Adraca/linux-lts-silent-fix-oracle/actions/workflows/ci.yml)
[![Tests](https://img.shields.io/badge/tests-9%20unit%20%2B%204%20integration-blue)](tests/README.md)
[![License](https://img.shields.io/badge/license-Apache--2.0-green.svg)](LICENSE)

Security-relevant bug fixes merged into the upstream Linux kernel mainline frequently lack explicit stable backport tags (`Cc: stable@vger.kernel.org`), resulting in a critical coverage gap where Long Term Support (LTS) kernel branches remain vulnerable to publicly documented bugs. Empirical evaluation demonstrates that approximately 15% of security fixes merged upstream are silently omitted from regular stable backports at commit time, creating an asymmetric window of vulnerability across production infrastructure.

Today, `fixtriage` provides the foundational triage and evaluation pipeline to systematically detect these gaps. By ingesting commit histories across mainline and LTS branches, the tool extracts trailer metadata (such as `Fixes:`), filters out explicitly tagged commits, and scores unflagged fixes using a transparent, weighted keyword and trailer baseline that measures detection precision and recall against historical backport ground truth.

This project is the subject of an application to the NLnet Foundation (CodeSupply, round closing 3 November 2026). The project is evolving `fixtriage` into a continuous open-data oracle for software supply chain transparency. The expanded oracle integrates semantic patch analysis to out-evaluate keyword heuristics, continuously tracks active LTS release heads, and emits standards-compliant vulnerability metadata—translating Linux kernel Package URLs (PURLs) into actionable Open Source Vulnerability (OSV) records and OpenVEX impact declarations.

## Quickstart

```sh
git clone https://github.com/Adraca/linux-lts-silent-fix-oracle.git && cd linux-lts-silent-fix-oracle
pip install -e .
python -m fixtriage candidates --repo /path/to/mainline --since 2023-06-01
```

## Status

Status: prototype under active development. 9 unit tests pass out of the box; 4 integration tests require a local kernel checkout (see [tests/README.md](tests/README.md)).

## Documentation

- [Evaluation Baseline](docs/BASELINE.md) — Empirical methodology, sample sizes, and precision/recall sweep.
- [Roadmap](docs/ROADMAP.md) — NLnet project milestones M1–M4 and planned deliverables.
- [Security Policy](docs/SECURITY.md) — Reporting procedures for live kernel vulnerabilities and coordinated disclosure.
- [Test Suite & Integration Setup](tests/README.md) — Details on unit and integration tests and `FIXTRIAGE_KERNEL_REPO`.

## License

Licensed under the [Apache License, Version 2.0](LICENSE).
