# Interview Preparation Skills

## Goal

Prepare for the Euroclear NIPE3 role by building practical skills in:

- VS Code
- GitHub Copilot
- Python 3.8.20
- Python 3.12 migration awareness
- Pydantic
- Prefect 2.2
- LLM-based extraction
- deterministic post-processing
- financial document extraction

---

## Point 1 — Eurobonds

Status: In progress

I should be able to explain:

- what a bond is
- what a Eurobond is
- why issuers use Eurobonds
- why investors buy Eurobonds
- Euroclear's role in settlement, custody, and asset servicing
- why ISINs and reference data matter

Key sentence:

> Eurobonds are international bonds used by issuers to access global funding, and Euroclear provides infrastructure for settlement, custody, and asset servicing.

---

## Point 2 — VS Code + GitHub Copilot + Python

Status: In progress

Action items:

- [ ] Confirm VS Code is installed
- [ ] Confirm GitHub Copilot extension is active
- [ ] Confirm GitHub Copilot Chat works
- [ ] Confirm Python extension is installed
- [ ] Confirm Pylance is installed
- [x] Create/use a Python 3.8.20 environment
- [x] Create/use a project `.venv` based on Python 3.8.20
- [ ] Understand Python 3.8 syntax limitations
- [ ] Avoid Python 3.10+ syntax in production-style code
- [ ] Practice asking Copilot to explain code
- [ ] Practice asking Copilot to generate pytest tests
- [ ] Practice asking Copilot to refactor safely
- [ ] Practice reviewing AI-generated code manually

Important Python 3.8 compatibility notes:

- Project Python is managed with `pyenv local 3.8.20`
- Activate the project environment with `source .venv/bin/activate` before running pytest, Prefect, or dependency checks
- Use `Optional[str]` instead of `str | None`
- Use `List[str]` instead of `list[str]`
- Avoid `match/case`
- Avoid assuming newer standard library features

Interview sentence:

> I use Copilot as an accelerator, but I validate all output with tests, schemas, source documents, deterministic rules, and SME-reviewed ground truth.

---

## Point 3 — Pydantic and Prefect

Status: In progress

Setup confirmed:

- Pydantic 1.10.26 installed in `.venv`
- Prefect 2.2.0 installed in `.venv`
- pytest installed in `.venv`
- Running `python` or `prefect` outside `.venv` may not find these packages

Action items:

- [ ] Build a small Pydantic model for extracted bond data
- [ ] Validate required and optional fields
- [ ] Add sentinel values for missing/unknown data
- [ ] Build a small Prefect 2.2 flow
- [ ] Add task retries
- [ ] Add logging
- [ ] Understand task dependencies
- [ ] Understand flow failure handling

---

## Point 4 — Case Study

Status: Waiting for prospectus PDFs

Goal:

Build a small extraction prototype that:

- reads prospectus text
- extracts structured fields
- validates output with Pydantic
- applies deterministic post-processing rules
- handles ISIN candidates
- writes diagnostic output
- includes tests

Potential fields:

- issuer name
- ISIN
- currency
- coupon
- maturity date
- issue amount
- redemption date
- governing law
- listing market
- denomination

---

## Personal Preparation Principle

Do not only learn definitions.

For each preparation point:

1. Build a small artifact.
2. Test it.
3. Explain it.
4. Connect it to NIPE3.