# Skill: deck-builder

**Area:** Digital Product Production (sales & training collateral) · **Owner approval gates touched:** `publication` (never crossed) · **Status:** implemented & tested

## Purpose
Produce **editable .pptx** sales and training decks from a JSON outline so the owner edits a real file instead of starting from a blank slide. Two maintained outlines ship with the skill:
- `templates/sales-deck.json` — Digital Footprint Reports sales narrative (pricing left as a placeholder on purpose).
- `templates/training-deck.json` — analyst onboarding for the readiness → scan → draft → approve → final workflow.

## Reuses
- `python-pptx` for output; `ledger.py` for optional deliverable registration.

## Instructions
```bash
python3 agents/skills/deck-builder/build_deck.py agents/skills/deck-builder/templates/sales-deck.json
python3 agents/skills/deck-builder/build_deck.py my-outline.json --out agents/workspace/40_Sales_Training/custom.pptx --engagement eng-xxxx
```
Outline schema is documented at the top of `build_deck.py` (title / bullets with one nesting level / two-column / section slides / speaker notes). Default output: `agents/workspace/40_Sales_Training/<kind>-deck-<date>.pptx`.

## Permission boundaries
- MAY: write `.pptx` under `agents/workspace/40_Sales_Training/` (or `--out`), append a `draft` deliverable record when `--engagement` is given.
- MAY NOT: fill in prices, discounts or commitments (spending/publication decisions), upload to Slides/Drive, present or send to a customer, mark a deck final. Footer text defaults to a draft notice; keep it until the owner records a `publication` approval.

## Verification example (2026-10-04)
```
$ build_deck.py templates/sales-deck.json --engagement eng-001cee7bf7
deck      : agents/workspace/40_Sales_Training/sales-deck-2026-10-04.pptx  (8 slides, kind=sales)
ledger rec: del-f6956809f1 (draft)
$ build_deck.py templates/training-deck.json
deck      : agents/workspace/40_Sales_Training/training-deck-2026-10-04.pptx  (8 slides, kind=training)
```
Re-opened with python-pptx: 8 slides each, speaker notes present (slide 2 of the sales deck: "Open with the buyer's pain: time, consistency, defensibility."). Copies are in `agents/examples/`.

## Invocation prompt
> Use the deck-builder skill to produce a sales deck for "<audience, e.g. employment-law firms>" based on templates/sales-deck.json, adjusting the problem and what-you-receive slides to that audience. Leave pricing as a placeholder, keep the draft footer, and tell me the file path and slide count. Do not publish or share it.
