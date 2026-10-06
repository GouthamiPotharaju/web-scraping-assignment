# AI Usage

**Tool:** Claude (claude.ai)

## What I used it for
Generating the project skeleton and first versions of the scrapers, cleaning, validation and deduplication modules, `main.py`, unit tests and the README from the assignment brief and the reference document. I also used it to debug problems I found while running the code on my own machine.

## Representative prompts
1. "first 1 is reference material second is the assignment" (I attached both documents and asked it to build the project).
2. I pasted my terminal output and the first rows of my CSV and asked what was wrong.
3. I pasted the HTML of a book description and asked why the text was duplicated.
4. I pasted the result of a script that listed the two "The Star-Touched Queen" entries and asked how to fix the duplicate rule.

## AI-assisted parts
Almost all of the code (`scrapers/`, `processing/`, `main.py`, `tests/`) and the first README draft were AI-generated. I ran, tested and checked everything on my own machine and made the fixes below.

## Problems found and fixed after review
1. **Duplicated and garbled descriptions.** Inspecting the real CSV showed each description appeared twice and ended with `...more`, and one had broken accents. I checked the page HTML myself: the duplicate was in the website's own HTML, not a selector bug (the AI's first guess was wrong). I added `clean_description` and a unit test.
2. **Wrong duplicate rule.** The AI's rule for books was source + title. My first full run removed "The Star-Touched Queen" as a duplicate, but I checked the site and found two different books (GBP 46.02 and GBP 32.30). I changed the rule to source + title + price and added a test for this case. Final result: 1,100 rows, 0 duplicates.
3. **Mixed-up test files.** While applying a fix, test code ended up in the wrong file. I noticed that `pytest` collected 14 tests instead of 19, used `pytest -v` to find the cause, and corrected both files.
4. The AI could not reach the websites from its environment, so the first live run was mine. It also underestimated the run time (it said about 10 minutes; it takes about 22).

## Testing and verification
- 19 unit tests (cleaning, validation, deduplication, pagination with a fake session, missing elements, failed page); all pass.
- A smoke run with `--max-pages 2`, then a full run from a fresh virtual environment.
- Checked the first CSV rows against the website, then confirmed `summary_report.json`: 1,000 + 100 collected, 0 rejected, 0 duplicates, 0 failed URLs, `counts_reconcile: true`, and the CSV row count matches (1,100).
- One brief network drop during an earlier run was recovered by the retry logic (visible as warnings in the log).