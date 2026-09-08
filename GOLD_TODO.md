# Gold Verification TODO

Open each PDF and confirm/fill the ground-truth value for every field in
[benchmark/gold.json](benchmark/gold.json). Use `null` when a field is genuinely
absent or not applicable to the instrument.

Rules for values (must match extractor output conventions):
- `isin` — the ISIN of THIS security (labelled "ISIN Code"), not an underlying.
- `document_type` — exactly `Final Terms` or `Pricing Supplement`.
- `coupon_type` — exactly `fixed`, `floating`, or `zero`.
- `interest_payment_frequency` — `annual`, `semi-annual`, `quarterly`, or `monthly`.
- `aggregate_nominal_amount`, `coupon_rate`, `issue_price` — plain numbers (no `,`, `%`, or currency symbol).
- `maturity_date`, `issue_date` — ISO format `YYYY-MM-DD`.
- `currency` — 3-letter ISO code (e.g. `EUR`).
- `issuer_lei` — 20-character LEI.

---

## New documents to verify (7)

For each, `isin` is pre-filled from the filename; confirm it and fill the rest.

### 1. dbs / XS1821439368 (pricing-supplement)
File: `prospect documents/dbs/XS1821439368__pricing-supplement__5326de8edc.pdf`

- [ ] isin (pre-filled: XS1821439368)
- [ ] issuer_name
- [ ] currency
- [ ] aggregate_nominal_amount
- [ ] coupon_rate
- [ ] maturity_date
- [ ] issue_date
- [ ] governing_law
- [ ] listing
- [ ] document_type  (expected: Pricing Supplement)
- [ ] common_code
- [ ] clearing_systems
- [ ] specified_denomination
- [ ] form_of_notes
- [ ] coupon_type
- [ ] interest_payment_frequency
- [ ] issue_price
- [ ] seniority
- [ ] issuer_lei
- [ ] guarantor_name

### 2. goldman-sachs / XS2412851037
File: `prospect documents/goldman-sachs/XS2412851037__final-terms__ad7e95c020.pdf`

- [ ] isin (pre-filled: XS2412851037)
- [ ] issuer_name
- [ ] currency
- [ ] aggregate_nominal_amount
- [ ] coupon_rate
- [ ] maturity_date
- [ ] issue_date
- [ ] governing_law
- [ ] listing
- [ ] document_type
- [ ] common_code
- [ ] clearing_systems
- [ ] specified_denomination
- [ ] form_of_notes
- [ ] coupon_type
- [ ] interest_payment_frequency
- [ ] issue_price
- [ ] seniority
- [ ] issuer_lei
- [ ] guarantor_name

### 3. jpmorgan / XS2019032544
File: `prospect documents/jpmorgan/XS2019032544__final-terms__36b9699889.pdf`

- [ ] isin (pre-filled: XS2019032544)
- [ ] issuer_name
- [ ] currency
- [ ] aggregate_nominal_amount
- [ ] coupon_rate
- [ ] maturity_date
- [ ] issue_date
- [ ] governing_law
- [ ] listing
- [ ] document_type
- [ ] common_code
- [ ] clearing_systems
- [ ] specified_denomination
- [ ] form_of_notes
- [ ] coupon_type
- [ ] interest_payment_frequency
- [ ] issue_price
- [ ] seniority
- [ ] issuer_lei
- [ ] guarantor_name

### 4. morgan-stanley / XS2403038255
File: `prospect documents/morgan-stanley/XS2403038255__final-terms__7abefd49a9.pdf`

- [ ] isin (pre-filled: XS2403038255)
- [ ] issuer_name
- [ ] currency
- [ ] aggregate_nominal_amount
- [ ] coupon_rate
- [ ] maturity_date
- [ ] issue_date
- [ ] governing_law
- [ ] listing
- [ ] document_type
- [ ] common_code
- [ ] clearing_systems
- [ ] specified_denomination
- [ ] form_of_notes
- [ ] coupon_type
- [ ] interest_payment_frequency
- [ ] issue_price
- [ ] seniority
- [ ] issuer_lei
- [ ] guarantor_name

### 5. soc-gen / XS1073721133
File: `prospect documents/soc-gen/XS1073721133__final-terms__e27893eb3e.pdf`

- [ ] isin (pre-filled: XS1073721133)
- [ ] issuer_name
- [ ] currency
- [ ] aggregate_nominal_amount
- [ ] coupon_rate
- [ ] maturity_date
- [ ] issue_date
- [ ] governing_law
- [ ] listing
- [ ] document_type
- [ ] common_code
- [ ] clearing_systems
- [ ] specified_denomination
- [ ] form_of_notes
- [ ] coupon_type
- [ ] interest_payment_frequency
- [ ] issue_price
- [ ] seniority
- [ ] issuer_lei
- [ ] guarantor_name

### 6. ubs / XS2637963146
File: `prospect documents/ubs/XS2637963146__final-terms__b1b67564ba.pdf`

- [ ] isin (pre-filled: XS2637963146)
- [ ] issuer_name
- [ ] currency
- [ ] aggregate_nominal_amount
- [ ] coupon_rate
- [ ] maturity_date
- [ ] issue_date
- [ ] governing_law
- [ ] listing
- [ ] document_type
- [ ] common_code
- [ ] clearing_systems
- [ ] specified_denomination
- [ ] form_of_notes
- [ ] coupon_type
- [ ] interest_payment_frequency
- [ ] issue_price
- [ ] seniority
- [ ] issuer_lei
- [ ] guarantor_name

### 7. hsbc / XS2994729221
File: `prospect documents/hsbc/XS2994729221.pdf`

- [ ] isin (pre-filled: XS2994729221)
- [ ] issuer_name
- [ ] currency
- [ ] aggregate_nominal_amount
- [ ] coupon_rate
- [ ] maturity_date
- [ ] issue_date
- [ ] governing_law
- [ ] listing
- [ ] document_type
- [ ] common_code
- [ ] clearing_systems
- [ ] specified_denomination
- [ ] form_of_notes
- [ ] coupon_type
- [ ] interest_payment_frequency
- [ ] issue_price
- [ ] seniority
- [ ] issuer_lei
- [ ] guarantor_name

---

## Existing documents — newly added fields to confirm (optional)

These 3 were previously partially labelled. Standardizing to the full field set
added the fields below as `null`. Confirm they are truly absent, or fill a value.

### barclays / XS0876756452
- [ ] governing_law
- [ ] listing
- [ ] clearing_systems
- [ ] specified_denomination
- [ ] form_of_notes
- [ ] issuer_lei

### bnp-paribas / XS2955926998
- [ ] currency
- [ ] aggregate_nominal_amount
- [ ] maturity_date
- [ ] listing
- [ ] common_code
- [ ] specified_denomination
- [ ] interest_payment_frequency
- [ ] issue_price
- [ ] seniority

### hsbc / XS2904540775
- [ ] governing_law
- [ ] listing
- [ ] common_code
- [ ] clearing_systems
- [ ] specified_denomination
- [ ] form_of_notes
- [ ] coupon_type
- [ ] interest_payment_frequency
- [ ] issue_price
- [ ] seniority
