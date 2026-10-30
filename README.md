# VC Data Normalizer

A `nanoagent.plugin/v0001` plugin, built on the structure of NanoAgent's reference plugin,
[arxiv-source](https://github.com/zeyuyang8/arxiv-source). Startup data arrives messy: funding written as
`$5.5M Series A`, `€20 million seed` or `¥3000万`, and YC batches as `W24`, `s2013` or `Summer '21`. The agent
normalizes each record into whole US dollars, a funding round, a batch season and a year, with totals. It
runs offline with a fixed rate table (USD 1, EUR 1.08, GBP 1.27, CNY 0.14), so every run converts the same way.

## Tools

| Tool | Does | Code |
|---|---|---|
| `parse_funding` | Parses funding texts: disclosed or not, currency, exact amount, round | `src/plugin/normalize.py` |
| `convert_to_usd` | Converts amounts to whole US dollars with the fixed rate table, halves away from zero | `src/plugin/normalize.py` |
| `parse_batch` | Parses YC batch texts into season and four-digit year | `src/plugin/normalize.py` |

### Tasks

| Task | Does | Runner |
|---|---|---|
| `normalize-records` | Normalizes 1 to 15 raw records and totals their disclosed funding | `agent`, with all three tools; no reference |

Example input: `{"records": [{"company": "Stripe", "funding": "€20 million seed", "batch": "S09"},
{"company": "Groww", "funding": "Undisclosed", "batch": "W18"}]}`.

### Verifier

`verify_task` applies the rules in `verifier/rules.py` to the task's own input and compares every
record: `one-per-record`, `same-companies` (names and order), `usd-only-when-disclosed`,
`disclosed-exact`, `funding-usd-exact`, `stage-exact`, `season-exact`, `year-exact`, `total-usd` and
`undisclosed-count`. Each tool call is checked the same way (`verifier/tools.py`). A text the rules cannot
read (no currency, two amounts, two rounds, extra words, an unknown batch) is refused, never guessed.
`tests/test_rules.py` pins the rules against hand-worked answers.

## Layout

```text
.
├── nanoagent.yaml   # manifest: id, runtime, permissions, tools, tasks
├── contract.py      # each tool's and task's typed input and output
├── src/plugin/      # the MCP server (__main__.py) and normalize.py
├── tests/           # rule tests and verifier tests: correct, wrong, missing, malformed and boundary cases
├── ui/              # renderers (outputs drawn from their JSON Schema)
├── product/         # product page: product.yaml and icon.svg
└── verifier/        # deterministic verifier: rules.py, tools.py, task.py, checks.py
```

## Develop and run

```bash
uv sync --extra dev
uv run pytest
uv run ruff check .
```

Publishing checks every plugin rule: push the plugin to a public GitHub repository and submit its URL
on RUSH Lab's Marketplace.
