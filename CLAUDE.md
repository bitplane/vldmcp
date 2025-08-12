# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Build and Development
```bash
# Install dependencies and prepare for development
make dev

# Run all tests
make test

# Run pre-commit hooks
pre-commit run --all-files

# Clean all build artifacts
make clean
```

## CODING STANDARDS

* IMPORTANT: DON'T USE IMPORT IN FUNCTIONS
* Python 3.10+ required. So type hints rarely need `typing` module.
* Line length for code: 120 characters (configured in `pyproject.toml`).
* Line length for Markdown is 80 wide so it fits in a standard terminal.
* All imports should be at module level (not in functions).
* The project will degrade into verbose, brittle spaghetti if left unchecked.
  Periodically propose simplifications.
* Branches are a source of shame and disgust. They should be used sparingly.
* Defensive programming is for the weak.
* Do not guess, read the docs. All the files are in source control or in the
  `.venv` dir at the project root.
* Also, don't use includes in functions.

### Testing

* Use `pytest` functional style for tests. No `TestClassBasedTestBSThanks`
* When there's a bug, write a test case for the component.
* Failing tests are good tests; they tested something. Don't write tests to
  pass, they are adversarial.
* The only functionality that is required, is functionality that is covered by
  a test. The only exception to this is where it has a comment that explains
  what it supposed to do, why it is important enough to exist yet simultaneously
  not important enough to be covered by a test. Tests
* Do not use mocks in tests unless required; they make a mockery of our
  codebase.
* And once again, it's important to remember: Don't use import in functions.
