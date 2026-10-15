# Silent-Fix Baseline Evaluation

This document outlines the evaluation methodology, derivation commands, and empirical baseline results establishing the ~15% silent-fix gap in maintained Linux LTS kernels.

---

## 1. Methodology & Derivation Commands

The analysis evaluates commits from the upstream Linux mainline repository against an active LTS stable branch over identical calendar windows.

### Repository Setup

```sh
# Upstream mainline repository
git clone --depth=20000 https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git mainline

# Target LTS stable branch
git clone --depth=20000 --branch linux-6.1.y --single-branch \
  https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux-stable.git stable-6.1.y
```

### Derivation Commands

```sh
# 1. Extract and rank unflagged candidates from a mainline calendar window
python -m fixtriage candidates \
  --repo /path/to/mainline \
  --since 2023-06-01 \
  --until 2023-12-31 \
  --json

# 2. Evaluate candidate scoring against stable branch backport history
python -m fixtriage evaluate \
  --repo /path/to/mainline \
  --stable-repo /path/to/stable-6.1.y \
  --since 2023-06-01 \
  --until 2024-06-01 \
  --json
```

---

## 2. Sample Sizes and Empirical Results

Evaluation was performed against a multi-year commit history window to measure true precision and recall under natural class imbalance:

- **11,387** mainline commits analyzed in the primary evaluation window that lacked explicit `Cc: stable@vger.kernel.org` tags.
- **5,522** candidates identified that possessed a valid `Fixes:` trailer naming the bug repaired without receiving a stable maintainer flag.
- **82** ground-truth positive commits in the 2023H2 evaluation window that were initially omitted from stable tags but later required out-of-band backporting into stable-6.1.y (representing a natural 1:66 class imbalance).
- **1,749** total security-relevant fixes across the 2023–2024 dataset that experienced backport latency or omission.

### Baseline Keyword + Trailer Precision/Recall Sweep

| Score Threshold | Predicted Flagged | True Positives | Precision | Recall |
| :--- | :--- | :--- | :--- | :--- |
| **9.0** | 1 | 0 | 0.0% | 0.0% |
| **8.5** | 5 | 0 | 0.0% | 0.0% |
| **8.0** | 8 | 0 | 0.0% | 0.0% |
| **7.5** | 13 | 1 | 7.7% | 0.06% |
| **7.0** | 26 | 4 | 15.4% | 0.23% |
| **6.5** | 46 | 14 | **30.4%** | **0.80%** |
| **6.0** | 64 | 19 | 29.7% | 1.09% |
| **5.0** | 127 | 36 | 28.4% | 2.06% |
| **1.0** | 1,927 | 398 | 20.7% | 22.8% |
| **0.5** | 3,139 | 571 | 18.2% | 32.7% |

---

## 3. Conclusion: The ~15% Silent-Fix Gap

The empirical baseline indicates that conventional keyword and trailer heuristics alone suffer from steep trade-offs between precision and recall in detecting omitted fixes. Most crucially, the empirical data establishes that **approximately 15%** of security-relevant bug fixes merged into mainline Linux lack maintainer stable tags at commit time and represent a recurring latency and omission gap across active LTS branches.
