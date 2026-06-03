# NSE Verification — Handoff Prompt for Claude in Chrome

Use this prompt to verify the NoSketchEngine deployment is working correctly.
Navigate to the URL below and paste this prompt into the Claude Chrome extension.

**URL:** https://noske-turkunlp-noske-dev.apps.lumi-k.eu

---

## Prompt

You are verifying a NoSketchEngine (corpus query interface) deployment serving a toy Finnish corpus (HPLT Toy, ~1000 documents of Finnish web text).

Please carry out the following checks and report the result of each:

1. **Page loads** — Does the Crystal UI load without errors? Note the page title and any visible corpus selector.

2. **Corpus selector** — Is "HPLT Toy" (or `hplt_toy`) listed as an available corpus? Select it.

3. **Basic word search** — Search for a common Finnish word, e.g. `[word="ja"]` in CQL mode (or just `ja` in simple mode). Do concordance lines appear? Do they look like real Finnish text?

4. **Frequency list** — If accessible, check the word frequency list for the corpus. Does it return a list of Finnish words?

5. **Structural attribute filter** — Try filtering by document metadata. In CQL: `[word=".*"] within <doc lang="fin_Latn"/>`. Do results return? (This verifies the structural attributes `lang`, `id`, `url` are indexed correctly.)

6. **Error check** — Are there any visible error messages, broken UI elements, or signs that the corpus is empty or not loaded?

Report: pass/fail for each check, plus any error messages verbatim.
