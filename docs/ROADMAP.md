# Project Roadmap: Linux LTS Silent Fix Oracle

This roadmap outlines the milestones and deliverables supported by the NLnet Foundation for developing an automated, open-data oracle that identifies unflagged Linux LTS kernel backport gaps and emits standards-compliant advisory statements (PURL in, OSV/OpenVEX out).

---

## Milestone 1 (M1): Corpus Ingestion & Baseline Triage Engine
- **Objective:** Establish the foundational multi-branch git ingestion pipeline and reproducible ground-truth evaluation harness.
- **Deliverables:**
  - Scalable Git commit and trailer parsing for mainline and LTS stable trees (5.15, 6.1, 6.6, 6.12).
  - Mechanical candidate extraction identifying commits that repair bugs (`Fixes:`) without stable flags (`Cc: stable@`).
  - Empirical baseline evaluation against historical backport outcomes establishing benchmark precision and recall.

---

## Milestone 2 (M2): Semantic Patch Analysis & Enhanced Classification
- **Objective:** Move beyond keyword and trailer heuristics to semantic change analysis.
- **Deliverables:**
  - Structural diff analysis and syntactic code change categorization.
  - Multi-signal scoring integrating author, subsystem topology, bug class weighting, and temporal backport decay.
  - Verification harness demonstrating classification performance superior to the keyword+trailer baseline.

---

## Milestone 3 (M3): Standards-Compliant Export (PURL, OSV, OpenVEX)
- **Objective:** Interoperate with modern software supply chain security standards.
- **Deliverables:**
  - Linux kernel Package URL (`pkg:generic/linux` and distro-specific PURLs) resolution.
  - Open Source Vulnerability (OSV) schema export for identified silent-fix gaps.
  - OpenVEX statement generation declaring vulnerability impact states (affected, fixed, not_affected) across active LTS branches.

---

## Milestone 4 (M4): Continuous Oracle Pipeline & Public Data Distribution
- **Objective:** Deploy continuous monitoring and open data distribution.
- **Deliverables:**
  - Automated continuous tracking against active Linux LTS release heads.
  - Publicly accessible data oracle feeding upstream maintainers and downstream distribution builders.
  - Integration documentation and CLI tools for automated SBOM/VEX consumption in CI/CD environments.
