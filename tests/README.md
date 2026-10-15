# Test Suite & Integration Test Setup

The test suite consists of **9 unit tests** and **4 real-data integration tests** (13 total).

---

## 1. Unit Tests (9 tests — Out of the Box)

The 9 unit tests in `tests/test_keywords.py` and `tests/test_trailers.py` validate trailer parsing and keyword scoring deterministically using embedded fixtures (such as `tests/fixtures/real_stable_backport.txt`). They run in milliseconds and require no external kernel repository:

```sh
pytest tests/test_keywords.py tests/test_trailers.py
```

---

## 2. Integration Tests (4 tests — Real Kernel Trees)

The 4 integration tests in `tests/test_integration.py` test end-to-end execution against real Linux Git commit histories:
1. `test_ingest_real_mainline_window`: Verifies log walking, SHA formatting, and commit metadata ingestion over a 1-year window (>1,000 commits).
2. `test_candidates_are_a_real_subset_with_fixes_and_no_cc_stable`: Verifies mechanical candidate filtering (`Fixes:` present, no `Cc: stable@`).
3. `test_ground_truth_extraction_finds_real_backports`: Extracts and validates upstream commit references (`commit <sha> upstream.`) from an active LTS branch.
4. `test_evaluate_end_to_end_on_a_window_old_enough_to_have_backports`: Runs the complete classification and evaluation pipeline and verifies recall curve monotonicity.

### Running Integration Tests Locally

Point `FIXTRIAGE_KERNEL_REPO` at a local kernel checkout:

```sh
FIXTRIAGE_KERNEL_REPO=/path/to/linux-kernel pytest tests/
```

Or set `KERNEL_MAINLINE` and `KERNEL_STABLE` individually if you maintain separate worktrees:

```sh
KERNEL_MAINLINE=/path/to/mainline KERNEL_STABLE=/path/to/stable-6.1.y pytest tests/
```

### Obtaining Working Shallow Clones

Because full kernel histories exceed several gigabytes, integration testing works against shallow clones covering the evaluation windows:

```sh
git clone --depth=20000 https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git mainline
git clone --depth=20000 --branch linux-6.1.y --single-branch \
  https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux-stable.git stable-6.1.y
```
