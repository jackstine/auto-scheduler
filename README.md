# Auto Scheduler

Using OpenRouter AI models to generate a scheduler for you.

## Overview

Auto Scheduler crawls community event websites, extracts structured event data using LLM agents, and produces a sorted JSON schedule. Point it at a list of URLs and get back a clean, deduplicated list of upcoming events.

## How It Works

1. **Crawl** — reads URLs from `links.txt`, downloads each site as markdown
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

2. run

```bash
uv run python -m src.main        # run the pipeline
```

Output lands in `output/raw_output.json`. Logs go to `output/run.log` and stdout.

### Testing

```bash
uv run pytest tests/ -v           # unit + integration (no LLM calls, free)
uv run pytest tests/ -v -m llm    # LLM integration tests (costs money)
uv run pytest tests/ -v -m ""     # everything
```

## Configuration

Edit `config.yaml` to adjust settings:

| Setting                | Default                  | Description                        |
|------------------------|--------------------------|------------------------------------|
| `max_sites`            | `0` (all)                | Limit sites to crawl (for testing) |
| `max_retries`          | `3`                      | Agent retry attempts on failure    |
| `max_concurrent_agents`| `3`                      | Parallel agent limit               |
| `model`                | `openrouter/aurora-alpha` | OpenRouter model to use           |

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
