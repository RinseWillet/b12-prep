# Agent Instructions

## Response Style

- Be concise.
- Prefer direct answers.
- Avoid long theoretical explanations unless explicitly requested.
- Use bullet points where possible.
- Focus on practical next steps.
- When explaining interview preparation, distinguish between:
  - concepts to understand
  - actions to perform
  - artifacts to create

## Project Context

This repository is used for preparation for a Euroclear NIPE3-related role.

Relevant topics:

- Python 3.8.20 compatibility
- future Python 3.12+ migration
- VS Code
- GitHub Copilot workflows
- Pydantic
- Prefect 2.2
- LLM-based financial document extraction
- Eurobond prospectus extraction
- deterministic post-processing
- reference data
- ISIN resolution
- regression tests
- SME-reviewed ground truth

## Python Rules

Assume production-style code should be Python 3.8-compatible unless stated otherwise.

Use:

- `Optional[str]` instead of `str | None`
- `List[str]` instead of `list[str]`
- `Dict[str, Any]` instead of `dict[str, Any]`

Avoid:

- `match/case`
- Python 3.10+ syntax
- unnecessary dependencies
- untested business logic

## AI-Assisted Development Rules

AI suggestions must be reviewed.

Generated code should be checked for:

- correctness
- Python 3.8 compatibility
- test coverage
- maintainability
- data-quality impact
- deterministic behavior
- explainability

Do not treat LLM output as truth.

For extraction logic, prefer:

1. structured output
2. schema validation
3. deterministic post-processing
4. reference-data checks
5. diagnostic reporting
6. regression tests

## Interview Preparation Rules

When asked to help prepare, provide:

- a short interpretation
- concrete action items
- suggested files or exercises
- interview-ready wording

Avoid generic motivational advice.