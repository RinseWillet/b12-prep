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

Wat EuroClear volgens mij vooral doet is de hele effectenhandel in o.a. EuroBonds, dus data en het veilig opslaan van effecten voor investeerders is een belangrijke taak, maar ook de hulp bij de settlement (d.w.z. het overbrengen van geld van investeerder naar issuer) - bij elke verhandeling van een Eurobond na issueing, moet weer een settlement worden gedaan - dus data en data security is heel belangrijk!

ISIN - International Securities Identification Number - this number identifies a specific financial security (een effect)

Okay, what have I just vibe coded:

I build a small system that uses an LLM, combined with prefect and pydantic to parse mainly prospectus and other files in pdf and extract from each one:

    isin, issuer_name, currency, aggregate_nominal_amount, coupon_rate, maturity_date, issue_date, governing_law, listing, document_type

The LLM used now is a locally installed model (Ollama) - the reason being to not burn tokens without reason (a LLM stub only gets you so far during development)

Functionality:
1) __main__.py parses the --source-dir and --output-dir values for the location of the pdfs
2) Then calls prospectus_extraction_flow(source_dir=..., output_dir=...)
3) In prospectus_extraction_flow, a Prefect orchestration layer is used for the pdf extraction pipeline
This layer: a) discovers the pdfs, b) extracts the texts per file c) runs the run_extraction which makes an LLM extraction (Ollama - local) or regex extraction if no model is available (fallback) d) does postprocessing using rules.py (in postprocessing) - this normalizes dates into Python date objects, currency codes, strips comma's from nominal amounts, it checks the ISIN number with the ISO 6166 definition, attaches confidence values and extraction method metadata e) then returns everything back to the prospectus_extraction_flow, which writes away a json file with all the extracted info and a filename based on the original filename. f) optionally, a diagnostics can be run to check all the extracted files and summarize the fields that have been extracted and the confidence levels

HOW TO run this little program:

In the terminal in the project run:

source .venv/bin/activate

This activates the virtual environment in which Prefect and Pydantic and others are installed. Then run:

python -m my_package --source-dir "prospect documents/barclays" --output-dir extraction_output

or

python -m my_package --source-dir "prospect documents/bnp-paribas" --output-dir extraction_output/bnp-paribas-ollama

if you want to be more specific where you want the extracted files to be located and the name even includes the llm type. This runs the extraction pipeline, and you end up with a bunch of json files.

Then (optionally) you can run the diagnostics:

python -c "
from my_package.reporting.diagnostics import write_diagnostics_csv
write_diagnostics_csv('extraction_output/bnp-paribas-ollama', 'extraction_output/diagnostics_bnp-pariba-ollama.csv')
"

This loops over all the jsons and provides a summary in .csv on the the extracted fields, whether the ISIN checksum was okay, and the confidence levels per extracted field. 
