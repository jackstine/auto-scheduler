# Event Scheduler - Application Specification

## Overview

A LangGraph-based pipeline that crawls community event websites, extracts structured event data via LLM agents, aggregates results, filters out past events, and produces a sorted JSON output.

## Pipeline

```
links.txt → Crawl Sites (parallel, or skip) → Parse (LLM agents, parallel) → Validate → Aggregate → Filter Past → Sort by Date → Output JSON
```

### Stage 1: Crawl

- Read URLs from `links.txt` (one URL per line, skip blanks, deduplicate)
- Delete all files in `output/` before starting (unless `skip_crawl` is enabled)
- All crawls run **concurrently** using async I/O, limited by `max_concurrent_crawls`
- For each URL, run the `crwl` CLI tool to download site content as markdown
- Save each result to `output/crawled/<safe_filename>.md`
- If a crawl fails for a site, log the error and continue to the next site
- Configurable: `max_sites` limits how many sites to crawl (for testing)
- Configurable: `max_concurrent_crawls` limits how many crawls run in parallel (default: 5)

#### Skip Crawl Mode

- When `skip_crawl` is `true` (config) or `--skip-crawl` is passed on the command line, the crawl stage is skipped entirely
- The pipeline reuses existing markdown files found in `output/crawled/`
- The `output/` directory is **not** cleared — only `parsed/` subdirectories are reset
- This is useful for re-running parsing/aggregation without re-downloading content
- If `skip_crawl` is enabled but `output/crawled/` is empty or missing, the pipeline logs a warning and continues with an empty file list

### Stage 2: Parse

- For each crawled markdown file, invoke an LLM agent via OpenRouter
- The agent receives the markdown content and a prompt instructing it to extract events as a JSON array
- Agents run in parallel (up to `max_concurrent_agents`)
- The agent is prompted to return only a JSON array of event objects
- The source URL is derived from the filename (reverse the filename encoding from crawl step)
- Prompt template is stored in `prompts/parse_schedule.md`

### Stage 3: Validate

- Each agent response is validated:
  - Must be valid JSON
  - Must be an array
  - Each object in the array is validated individually:
    - Only fields from the allowed schema are present (unknown fields cause that object to be rejected)
    - Missing optional fields are acceptable
    - Objects that fail validation are discarded; valid objects are kept
- If the entire agent response fails validation (not valid JSON, not an array), retry with a fresh agent context
- Configurable: `max_retries` (default: 3) — number of retry attempts per file before giving up
- Raw agent responses saved to `output/parsed/pre_validation/`
- Validated objects saved to `output/parsed/post_validation/`

### Stage 4: Aggregate

- Combine all valid event objects from all parsed files into a single list
- Inject `source_url` into each event object (derived from filename)

### Stage 5: Filter

- Remove any events where `date` is before today's date (determined at runtime)

### Stage 6: Sort & Output

- Sort remaining events by `date` ascending, then by `time` ascending
- Write final JSON array to `output/raw_output.json`

## Data Model

### Event Object

```json
{
  "name": "AIMUG Monthly Mixer & Showcase",
  "date": "2026-02-04",
  "time": "18:00",
  "time_zone": "CST",
  "venue": "Cloudflare Office",
  "address": "405 Comal St, Austin TX",
  "event_url": "https://www.meetup.com/austin-langchain-ai-group/events/312282689/",
  "source_url": "https://www.meetup.com/austin-langchain-ai-group/",
  "description": "Monthly mixer with demos, talks, and networking"
}
```

### Field Definitions

| Field       | Type   | Required | Description                                      |
|-------------|--------|----------|--------------------------------------------------|
| name        | string | yes      | Name of the event                                |
| date        | string | yes      | Date of the event, format `YYYY-MM-DD`           |
| time        | string | yes      | Time of the event, format `HH:MM` (24hr)         |
| time_zone   | string | no       | Time zone abbreviation (e.g., CST, CDT)          |
| venue       | string | no       | Venue name                                       |
| address     | string | no       | Address of the venue                             |
| event_url   | string | no       | Direct link to the event page                    |
| source_url  | string | no       | Link to the originating site that was crawled    |
| description | string | no       | Brief description of the event                   |

### Allowed Fields

Only the fields listed above are permitted on each event object. Any object containing a field not in this list is rejected during validation.

## Configuration

Configuration is provided via `config.yaml`. Defaults are used when not specified.

| Setting                | Type    | Default                  | Description                                          |
|------------------------|---------|--------------------------|------------------------------------------------------|
| links_file             | string  | `links.txt`              | Path to file containing URLs to crawl                |
| output_dir             | string  | `output`                 | Directory for all output files                       |
| max_sites              | integer | 0 (no limit)             | Max number of sites to crawl; 0 means all            |
| max_retries            | integer | 3                        | Max retry attempts per agent on validation failure   |
| max_concurrent_agents  | integer | 3                        | Max agents running in parallel                       |
| max_concurrent_crawls  | integer | 5                        | Max crawls running in parallel                       |
| skip_crawl             | boolean | `false`                  | Skip crawling and reuse existing crawled files       |
| model                  | string  | `openrouter/aurora-alpha` | LLM model identifier for OpenRouter                 |
| crwl_command           | string  | `crwl`                   | CLI command used for crawling                        |
| crwl_pyenv_version     | string  | `3.13.1`                 | pyenv version to use for crwl command                |

## Logging

- All log output goes to `output/run.log` and stdout
- Log entries include: timestamp, stage, site/file, outcome (success/fail/retry), event counts

## Input

- `links.txt` — one URL per line, may contain duplicates (deduplicate at runtime), may change over time

## Output

- `output/raw_output.json` — JSON array of event objects, sorted by date then time ascending, with past events excluded
