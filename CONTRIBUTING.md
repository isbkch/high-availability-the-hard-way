# Contributing to High Availability The Hard Way

Thank you for your interest! This project is an educational platform for reliability engineering.

## Ways to Contribute

1. **Add a new lab** — Follow the existing lab structure
2. **Improve existing labs** — Better explanations, clearer failure modes
3. **Add documentation** — Concepts, case studies, checklists
4. **Fix bugs** — Labs that don't work, broken scripts
5. **Share your experience** — Blog posts, talks, case studies

## Lab Structure

Every lab must have:
- `README.md` with clear instructions
- `before/` and `after/` code
- Scripts to run, break, and reset
- Tests proving the failure and the fix
- Production readiness checklist

## Principles

1. Failures must be real (no mock failures)
2. Setup must be trivial (one command)
3. Prove everything (tests, load tests)
4. Respect the learner's time

## Pull Request Process

1. Fork the repo
2. Create a branch for your lab
3. Follow the existing structure
4. Test your lab thoroughly
5. Submit PR with clear description

## Code Style

- Python: Follow PEP 8
- Bash: Use ShellCheck
- Markdown: Use markdownlint
