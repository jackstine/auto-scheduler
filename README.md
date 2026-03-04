# Auto Scheduler

Using OpenRouter AI models to generate a scheduler for you.

## Overview

Auto Scheduler crawls community event websites, extracts structured event data using LLM agents, and produces a sorted JSON schedule. Point it at a list of URLs and get back a clean, deduplicated list of upcoming events.

## How It Works

1. **Crawl** — reads URLs from `links.txt`, downloads each site as markdown **concurrently** (or skip with `--skip-crawl`)
2. **Parse** — sends each markdown file to an LLM agent (via OpenRouter) to extract events as JSON
3. **Validate** — checks agent output for valid JSON and schema compliance, retries on failure
4. **Aggregate, Filter & Sort** — combines all events, removes past dates, sorts by date/time, writes output

## How To Use

### Setup

```bash
uv sync                          # install dependencies
cp .env.example .env             # add your OPENROUTER_API_KEY
```

### Operate
1. setup the `links.txt` page

```markdown
meetup.com/<org>
meetup.com/<org1>
hackerspaceCity.com/events
```

2. add in [config.yaml](docs/config.md)

3. run it

```bash
uv run python -m src.main            # run the full pipeline
uv run python -m src.main --skip-crawl  # skip crawling, reuse existing files
```

The `--skip-crawl` flag skips the crawl stage and reuses markdown files already in `output/crawled/`. Useful for re-running parsing without re-downloading.

Output lands in `output/raw_output.json`. Logs go to `output/run.log` and stdout.

### Testing

```bash
uv run pytest tests/ -v           # unit + integration (no LLM calls, free)
uv run pytest tests/ -v -m llm    # LLM integration tests (costs money)
uv run pytest tests/ -v -m ""     # everything
```

## Configuration

Copy the example and edit to taste. See [full config docs](docs/config.md) for details.

```bash
cp config.example.yaml config.yaml
```

| Setting                | Default                            | Description                        |
|------------------------|------------------------------------|------------------------------------|
| `max_sites`            | `0` (all)                          | Limit sites to crawl (for testing) |
| `max_retries`          | `3`                                | Agent retry attempts on failure    |
| `max_concurrent_agents`| `3`                                | Parallel agent limit               |
| `max_concurrent_crawls`| `5`                                | Parallel crawl limit               |
| `skip_crawl`           | `false`                            | Skip crawling, reuse existing files|
| `model`                | `arcee-ai/trinity-large-preview:free` | OpenRouter model to use         |
| `crwl_command`         | `crwl`                             | must install Crwl mentioned below in [What is crwl?](#what-is-crwl)|

## Project Structure

```
links.txt              # URLs to crawl (one per line)
config.yaml            # pipeline configuration
prompts/               # LLM prompt templates
src/                   # application source code
  graph.py             # LangGraph pipeline definition
  nodes/               # crawl, parse, validate, aggregate, filter_sort
tests/                 # unit and integration tests
output/                # generated at runtime (crawled, parsed, final JSON)
specs/                 # application specification
```
 
 ## Crawler of Choice 

 ### What is crwl?

 crwl is the command-line interface for crawl4ai
 (https://github.com/unclecode/crawl4ai) — an open-source AI-friendly web crawler.
 It:
 - Launches a headless Chromium browser (via Playwright) to load JavaScript-heavy
 pages
 - Converts the page content to clean Markdown that LLMs can easily read
 - Usage: crwl crawl <url> -o markdown

 That's exactly what the auto-scheduler needed — most of those Meetup.com and Luma
 pages don't work with a simple HTTP fetch because they render content via
 JavaScript.

 The crwl name on PyPI is actually a completely unrelated package (some random
 Korean project). crwl as a CLI lives inside the crawl4ai package.

 ### How I installed it

 Three steps:

 1. Installed uv (the Python package manager the project requires) via the official
 installer:
   ```bash
     curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
 2. Installed crawl4ai as a uv tool — this makes crwl available globally as a CLI
 command:
   ```bash
     uv tool install crawl4ai
   ```
 3. Downloaded Chromium (the headless browser crwl drives under the hood):
   ```bash
     uvx playwright install chromium
   ```

