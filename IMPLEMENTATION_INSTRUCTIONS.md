# Implementation Instructions

## Overview

This directory contains one or more approved Gherkin feature specifications in
the `specs/` folder. Your task is to:

1. Implement the application code that satisfies every scenario
2. Create a behave test suite that exercises the implementation

The test suite must be structured to be compatible with the Clarity Engine
Phase 2 reporting tool, which measures per-scenario code coverage and
complexity.

---

## Required Project Structure

```
project/
├── specs/                    # Approved Gherkin specs — do not modify
│   └── *.feature
├── src/                      # Application code (or use a package directory)
│   └── *.py
└── features/                 # Behave test suite
    ├── *.feature             # Behave feature files (see rules below)
    └── steps/
        └── steps.py          # Step definitions
```

---

## Implementing the Application Code

- Read every file in `specs/` before writing any code.
- Implement whatever modules, classes, or functions are needed to satisfy all
  scenarios across all specs.
- Keep the application code in `src/` (or a named package directory) and
  separate from the test infrastructure in `features/`.

---

## Writing the Behave Test Suite

### Feature files

Create one or more `.feature` files inside `features/`. These files describe
the same scenarios as the specs but are written to drive your implementation
through its public interface.

**Critical rule — scenario names must match exactly:**
The reporting tool identifies scenarios by name. Every `Scenario:` and
`Scenario Outline:` name in `features/*.feature` must be an exact, character-
for-character match of the corresponding name in `specs/*.feature`. Do not
paraphrase, abbreviate, or reorder them.

Example — if `specs/foo.feature` contains:

```gherkin
Scenario: User resets their password successfully
```

then `features/foo.feature` must also contain:

```gherkin
Scenario: User resets their password successfully
```

### Step definitions

- Place all step definitions under `features/steps/`.
- Steps must import and call the actual application code — do not stub or
  mock the implementation inside step definitions. The reporting tool measures
  which lines of application code are exercised, so hollow steps produce
  meaningless metrics.
- Use `context` to share state between Given / When / Then steps within a
  scenario.

### All tests must pass

Run the suite before considering the implementation complete:

```bash
python -m behave features/
```

Every scenario must pass. The reporting tool will refuse to generate a report
for a project with failing tests.

---

## Checklist Before Handing Off to Phase 2

- [ ] `specs/` is present and unmodified
- [ ] All application code lives in `src/` (or a named package), not in `features/`
- [ ] `features/*.feature` exists with scenarios whose names exactly match `specs/*.feature`
- [ ] `features/steps/` contains step definitions that call the real implementation
- [ ] `python -m behave features/` exits with no failures
