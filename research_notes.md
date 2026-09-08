- What is a bond? A tradable loan issued out by a company, government etc. The act of buying the bond is essentially giving out the loan and the interest rate is often fixed. At some point the issuer must repay the outstanding loan
- Why bonds? Let's borrow as cheaply as possible or tap a market I otherwise do not have access too. (Interest rate tends to be a bit lower because the bonds are tradable)
- Investors are typically big pensionfund type of companies
- Domestic vs Foreign Bonds (e.g. for hedging capital in foreign currency for expansion in that monetary zone) (Foreign bonds like Samurai Bond, Yankee Bond, Aussi Bond) -> Domestic Bond = domestic currency in domestic country, Foreign Bonds = e.g. UK company issuing bonds in US in Dollars (local currency there). 
Eurobonds are based on the EuroCurrencies, but you can have EuroDollars, EuroYen - which are Dollars or Yen that are deposited in accounts outside the US or Japan respectively - EuroCurrencies are all these currencies deposited outside the domestic zone. So EuroEuro is even possible - the term Euro in EuroBond has to do with the history of these type of bonds (happening first for investors to get Dollars but not from the US directly and mostly happening in Europe) -> Ultimately, the Eurobond is a financial tool that allows companies to find the cheapest way to borrow money in a desired currency. You also spread the debt over various pools of people to borrow money from (not just US, Europe or ...) you can even use the bonds to swap and pay back earlier loans.
Eurobond markets is for big issuers (50 million dollars and up) - and typically with fixed interest rates
A copuple of terms: 
- the Issuer - company, bank etc. wanting to borrow money
- Investor - the entity or person lending the money (buying the bond)
- Coupon - interest payment
- Maturity - date when the issuer repays the principal
- Face value / principal - amount of money borrowed
- Yield - investors expected return
- Default - when the issuer cannot pay

from AI: “Eurobonds are important because they connect issuers seeking international funding with investors looking for global investment opportunities.”

“Euroclear is important in the Eurobond market because it provides infrastructure for settlement, custody, and asset servicing. Since Eurobonds are issued and traded internationally, they require trusted systems that can handle cross-border transactions reliably.”

Why Eurobonds? - Issuers:
- want to raise large amounts of money
- accessing global investors
- borrowing in a foreign currency
- diversifying funding sources
- potentially getting better borrowing terms
- avoiding dependence on one domestic market

Investors:
- international diversification
- exposure to different currencies
- access to foreign issuers
- potentially higher yields
- liquid international securities

Wat EuroClear volgens mij vooral doet is de hele effecten/obligatie handel in o.a. EuroBonds, dus data en het veilig opslaan van effecten voor investeerders is een belangrijke taak, maar ook de hulp bij de settlement (d.w.z. het overbrengen van geld van investeerder naar issuer) - bij elke verhandeling van een Eurobond na issueing, moet weer een settlement worden gedaan - dus data en data security is heel belangrijk!

ISIN - International Securities Identification Number - this number identifies a specific financial security (een effect)

Okay, what have I just vibe coded:

I build a small proof of concept system that uses an LLM, combined with prefect and pydantic to parse mainly prospectus and other files in pdf and extract from each one:

    isin, issuer_name, currency, aggregate_nominal_amount, coupon_rate, maturity_date, issue_date, governing_law, listing, document_type

The LLM used now is a locally installed model (Ollama) - the reason being to not burn tokens without reason (a LLM stub only gets you so far during development)

Functionality:
1) __main__.py parses the --source-dir and --output-dir values for the location of the pdfs
2) Then calls prospectus_extraction_flow(source_dir=..., output_dir=...)
3) In prospectus_extraction_flow, a Prefect orchestration layer is used for the pdf extraction pipeline
This layer: 
3a) discovers the pdfs, 
3b) extracts the texts per file 
3c) runs the run_extraction which makes an LLM extraction (Ollama - local) or regex extraction if no model is available (fallback)
3d) does postprocessing using rules.py (in postprocessing) - this normalizes dates into Python date objects, currency codes, strips comma's from nominal amounts, it checks the ISIN number with the ISO 6166 definition, attaches confidence values and extraction method metadata The postprocess phase or, more specifically, in the rules.py, is actually where ProspectusFields and ExtractedField are imported from prospectus.py and this file defines the dataschema used as result in the extraction-flow.
3e) then returns everything back to the prospectus_extraction_flow, which writes away a json file with all the extracted info and a filename based on the original filename. 
4) optionally, a diagnostics can be run to check all the extracted files and summarize the fields that have been extracted and the confidence levels

This setup uses the OpenAI SDK so this code is compatible with the use of OpenAI api's as well.



HOW TO run this little program:

In the terminal in the project run:

source .venv/bin/activate

This activates the virtual environment in which Prefect and Pydantic and others are installed. Then run:

python -m my_package --source-dir "prospect documents/barclays" --output-dir extraction_output

or

python -m my_package --source-dir "prospect documents/bnp-paribas" --output-dir extraction_output/bnp-paribas-ollama

if you want to be more specific where you want the extracted files to be located and the name even includes the llm type. This runs the extraction pipeline, and you end up with a bunch of json files.

If you want to run a specific LLM model (OLLAMA), you can do:

FOR BIG LLM:

source .venv/bin/activate
OLLAMA_MODEL=llama3.1:8b python -m my_package --source-dir "prospect documents/bnp-paribas" --output-dir extraction_output/bnp-paribas-ollama-8b

OR FOR SMALLER LLM (default):

source .venv/bin/activate
OLLAMA_MODEL=llama3.2:3b python -m my_package --source-dir "prospect documents/bnp-paribas" --output-dir extraction_output/bnp-paribas-ollama-3b

Then (optionally) you can run the diagnostics:

python -c "
from my_package.reporting.diagnostics import write_diagnostics_csv
write_diagnostics_csv('extraction_output/bnp-paribas-ollama', 'extraction_output/diagnostics_bnp-pariba-ollama.csv')
"

This loops over all the jsons and provides a summary in .csv on the the extracted fields, whether the ISIN checksum was okay, and the confidence levels per extracted field. 

## Extracted fields (extended for primary + secondary market reference data)

The schema now captures 20 fields. On top of the original 10 (isin, issuer_name,
currency, aggregate_nominal_amount, coupon_rate, maturity_date, issue_date,
governing_law, listing, document_type) it adds settlement/reference-data fields
that matter for a Euroclear-style CSD servicing issuance and investor-to-investor
settlement:

- common_code (Euroclear/Clearstream 9-digit), clearing_systems, specified_denomination, form_of_notes
- coupon_type (fixed/floating/zero), interest_payment_frequency, issue_price, seniority
- issuer_lei (ISO 17442), guarantor_name

## Benchmark: local Ollama vs regex stub vs a curated reference ("gold")

Goal: measure how well the local Ollama LLM performs against a stronger reference.
The reference ("gold") is a hand-curated set of expected values read straight from
3 source PDFs (benchmark/gold.json). The regex Stub is scored too as a baseline, so
each run is a three-way picture: Stub (regex) vs Ollama (local LLM) vs Gold.

How to run it (after activating the venv):

python -c "
from my_package.reporting.benchmark import run_benchmark
detail, summary = run_benchmark('benchmark/gold.json', 'extraction_output/benchmark.csv', mode='exact')
print(summary.to_string(index=False))
"

What it does: for each PDF in the gold file it extracts the text, runs every
available extractor (Stub always; Ollama only if a local server is reachable),
post-processes each result, and compares field-by-field to the gold values. Each
field is classified as match / mismatch / missing (extractor returned nothing) /
spurious (extractor invented a value the gold says is absent). It writes a detailed
long-format CSV (benchmark.csv: pdf, field, extractor, expected, actual, outcome)
plus a per-extractor accuracy summary (benchmark_summary.csv).

Two scoring modes:
- mode='exact'   -> literal comparison (case- and punctuation-sensitive).
- mode='lenient' -> case-insensitive + substring matching on text fields; use it to
  see how "near" the misses are (e.g. "FINAL TERMS" vs "Final Terms").

## Performance report (3 PDFs: Barclays vanilla bond, BNP structured certificate, HSBC fixed-to-floating; 35 scored fields each extractor)

| Extractor | Exact accuracy | Lenient accuracy |
| --------- | -------------- | ---------------- |
| Ollama (llama3.1:8b, local + ISIN override) | ~0.91 | ~0.91 |
| Ollama (llama3.2:3b, local + ISIN override) | ~0.86 | ~0.86 |
| Stub (regex baseline)       | 0.74  | 0.91 |
| Gold (reference)            | 1.00 (definition) | 1.00 |

(Stub numbers are after the ISIN-anchoring fix below; before it they were 0.71 / 0.89.
Ollama 3b is after the hybrid ISIN override below; before it it was ~0.83. The 8b row
is the larger-model experiment below.)

Key takeaways:
- The regex stub jumps from 0.71 to 0.89 under lenient scoring: almost all its
  "errors" were formatting noise (e.g. "FINAL TERMS" vs "Final Terms", a trailing
  full stop on "English law."), not wrong content.
- Ollama stays ~0.83 in both modes: its misses are genuine content errors, not
  formatting. Examples caught in a run:
  * inflated the Barclays aggregate nominal to 7,500,000,000 (extra zero)
  * dropped document_type on some docs (returned nothing)
  * called the BNP certificate a "Certificate" instead of "Final Terms"
- Both extractors grabbed a wrong reference ISIN (DE0001102473) that appears in the
  HSBC document before the real one (XS2904540775) - a shared weakness, not an LLM-
  specific one.
- Ollama output varies slightly run-to-run even at temperature=0 (28-29/35 matches),
  so treat single-run numbers as indicative, not exact.

## Is there a way to improve this?

Extraction quality:
- [DONE] Anchor the ISIN to its labelled field ("ISIN Code:" first, else "ISIN:")
  and take the last match, so reference ISINs of underlyings earlier in the
  document don't win. This fixed the stub's DE0001102473 error on the HSBC doc
  (stub now 3/3 ISINs correct; exact 0.71 -> 0.74, lenient 0.89 -> 0.91). Ollama
  still returns the wrong ISIN here - a model error, addressed by the structured-
  output/prompt fix below rather than by regex.
- [DONE] Give the LLM a typed output contract: Ollama now runs in JSON mode
  (response_format json_object) with a system prompt spelling out per-field rules
  (pick THIS security's ISIN, document_type exactly Final Terms/Pricing
  Supplement, coupon_type fixed/floating/zero, numbers with no separators/symbols/
  %, 20-char LEI). Effect: output is always valid JSON and document_type is now
  consistently "Final Terms" (was "FINAL TERMS"/"Certificate"/None). It did NOT
  fix the reference-ISIN pick or a wrong nominal on llama3.2:3b - the small model
  ignores those instructions, so the next lever is a larger model or a
  deterministic override that feeds the regex-anchored ISIN back over the LLM's.
- [DONE] Hybrid ISIN override: OllamaExtractor now overrides the LLM's isin with a
  strongly-labelled "ISIN Code" match (extract_labelled_isin) whenever one exists.
  This deterministically fixes the HSBC reference-ISIN error the 3b model would not
  fix itself, and lifts Ollama from ~0.83 to ~0.86 (3/3 ISINs correct). Applies in
  both the flow and the benchmark since both build OllamaExtractor.
- [DONE] Chunking (option B): instead of truncating to the first 12,000 chars, the
  OllamaExtractor now splits the text into overlapping windows (CHUNK_CHARS=12000,
  CHUNK_OVERLAP=500, capped at MAX_CHUNKS=6), runs the LLM per chunk, and merges
  field-by-field (first non-null wins). Each chunk fits the default Ollama context
  window, so no num_ctx change is needed, and the hard 12k ceiling is gone -
  documents longer than 12k (BNP, HSBC ~18.7k chars) are now seen in full, and huge
  files (KST books) stay bounded by the chunk cap. On the 3-PDF gold set the net
  accuracy is within Ollama's run-to-run noise (short Final Terms barely truncated),
  so the benefit is structural rather than visible here. Caveat: the naive "first
  non-null wins" merge can lock in an early wrong value (e.g. it grabbed
  clearing_systems="Global Security" from a form-of-notes line before the real
  "Euroclear..." appeared in a later chunk). A smarter merge (majority vote,
  confidence-weighted, or region-aware) is the natural follow-up. Trade-off:
  chunking multiplies the number of LLM calls, so extraction is noticeably slower.
- Normalise document_type to a canonical casing in post-processing so casing noise
  stops counting as an error even in exact mode.

Benchmark quality:
- Grow the gold set beyond 3 PDFs and across more issuers so accuracy numbers are
  statistically meaningful.
- Run Ollama N times per document and report mean/variance to account for the
  run-to-run drift.
- Add a per-field accuracy breakdown (which fields Ollama reliably gets vs fails) to
  target prompt/regex improvements.
- [DONE] Try a larger local model. Pulled llama3.1:8b and added a `models` argument
  to run_benchmark so several Ollama models are scored side by side in one run
  (each gets its own "ollama:<model>" column). Result: 8b reaches ~0.91 exact vs
  3b's ~0.86 - it fixed the inflated Barclays nominal and the wrong document_type,
  and its only remaining misses are soft (a missing coupon_type, one clearing_systems
  confusion, and returning "Not Applicable" instead of null for a guarantor). Run it:

  python -c "
  from my_package.reporting.benchmark import run_benchmark
  run_benchmark('benchmark/gold.json','extraction_output/benchmark.csv',
                mode='exact', models=['llama3.2:3b','llama3.1:8b'])
  "

  Trade-off: 8b is ~2.5x the size (4.9 GB) and slower per document than 3b.


## Benchmark harness — models, timing, prompts (2026-09)

Model line-up (add via `run_benchmark(models=[...])` or `OLLAMA_MODEL`):
- stub (regex baseline), llama3.2:3b, llama3.1:8b, qwen2.5:7b-instruct, qwen3:14b.
- Pull first: `ollama pull qwen2.5:7b-instruct` and `ollama pull qwen3:14b`.
- qwen3 emits `<think>` reasoning; OllamaExtractor appends `/no_think` and strips think tags so JSON stays clean.

Gold set: benchmark/gold.json now has 10 docs, every entry labels the full 20-field set
(null where absent). New docs' values still need SME verification — see GOLD_TODO.md.

Timing: benchmark detail CSV has a per-document `seconds` column; summary has
`avg_seconds_per_doc` so accuracy can be weighed against cost.

Prompt A/B: OllamaExtractor prompt is selectable via `prompt_variant` arg or
`OLLAMA_PROMPT_VARIANT` env ("v1" baseline, "v2" adds per-field hints + one worked
example). Benchmark v1 vs v2 before switching the default. Fine-tuning weights was
rejected — prompt engineering + a larger gold set is the higher-ROI, explainable path.
