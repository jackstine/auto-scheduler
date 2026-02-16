# Implementation Plan

## Architecture

```
                         ┌─────────────┐
                         │  links.txt  │
                         └──────┬──────┘
                                │
                         ┌──────▼──────┐
                         │    Crawl    │  (crwl CLI, sequential)
                         └──────┬──────┘
                                │
                      output/crawled/*.md
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
        ┌─────▼─────┐    ┌─────▼─────┐    ┌─────▼─────┐
        │  Agent 1  │    │  Agent 2  │    │  Agent N  │   (parallel, up to max_concurrent)
        └─────┬─────┘    └─────┬─────┘    └─────┬─────┘
              │                 │                 │
              │    retry loop (up to max_retries) │
              │    per agent if validation fails  │
              │                 │                 │
        ┌─────▼─────┐    ┌─────▼─────┐    ┌─────▼─────┐
        │ Validate  │    │ Validate  │    │ Validate  │
        └─────┬─────┘    └─────┬─────┘    └─────┬─────┘
              │                 │                 │
              └─────────────────┼─────────────────┘
                                │
                         ┌──────▼──────┐
                         │  Aggregate  │
                         └──────┬──────┘
                                │
                         ┌──────▼──────┐
                         │ Filter/Sort │  (remove past dates, sort asc)
                         └──────┬──────┘
                                │
                    output/raw_output.json
```

## Directory Structure

```
scheduler/
├── links.txt
├── config.yaml
├── prompts/
│   └── parse_schedule.md
├── output/                        # cleared at start of each run
│   ├── crawled/                   # markdown from crwl
│   │   ├── site_a.md
│   │   └── site_b.md
│   ├── parsed/
│   │   ├── pre_validation/        # raw agent JSON response
│   │   │   ├── site_a.json
│   │   │   └── site_b.json
│   │   └── post_validation/       # only valid event objects
│   │       ├── site_a.json
│   │       └── site_b.json
│   ├── raw_output.json            # final aggregated, filtered, sorted
│   └── run.log                    # pipeline log
├── src/
│   ├── __init__.py
│   ├── main.py                    # entry point
│   ├── config.py                  # load config
│   ├── graph.py                   # LangGraph graph definition
│   ├── nodes/
│   │   ├── __init__.py
│   │   ├── crawl.py               # crawl node
│   │   ├── parse.py               # agent parse node
│   │   ├── validate.py            # validation logic
│   │   ├── aggregate.py           # combine all post_validation JSONs
│   │   └── filter_sort.py         # filter past, sort, write output
│   └── utils.py                   # filename encoding/decoding, helpers
├── specs/
│   └── scheduler.md
└── IMPLEMENTATION_PLAN.md
```

## Configuration — `config.yaml`

```yaml
links_file: links.txt
output_dir: output
max_sites: 3                        # 0 = no limit
max_retries: 3
max_concurrent_agents: 3
model: openrouter/aurora-alpha
crwl_command: crwl
```

## LangGraph Graph

The graph has the following nodes and edges:

```
START → crawl → parse_all → aggregate → filter_sort → END
```

### Node: `crawl`
- Clear `output/` directory
- Read and deduplicate URLs from `links.txt`
- Apply `max_sites` limit
- For each URL, run `crwl <url> -o markdown` and save to `output/crawled/<safe_filename>.md`
- Log success/failure per site
- Pass list of crawled file paths to next node

### Node: `parse_all`
- For each crawled file, launch an agent call in parallel (up to `max_concurrent_agents`)
- Each agent call:
  1. Read the markdown file content
  2. Load prompt template from `prompts/parse_schedule.md` with today's date injected
  3. Call LLM via OpenRouter with the prompt + markdown content
  4. Save raw response to `output/parsed/pre_validation/<filename>.json`
  5. Validate the response:
     - Parse as JSON
     - Must be an array
     - Per object: reject if unknown fields present, keep if valid (missing optional fields OK)
  6. If entire response is invalid JSON or not an array → retry (fresh context, up to `max_retries`)
  7. Save valid objects to `output/parsed/post_validation/<filename>.json`
- Log per-file: success, retry count, number of events extracted

### Node: `aggregate`
- Read all files from `output/parsed/post_validation/`
- Combine into a single list
- Inject `source_url` into each event object (derived from filename)

### Node: `filter_sort`
- Remove events where `date` is before today
- Sort by `date` ascending, then `time` ascending
- Write to `output/raw_output.json`
- Log final event count

## Prompt — `prompts/parse_schedule.md`

The prompt instructs the agent to:
- Know today's date
- Read the provided markdown content
- Extract all events found
- Return only a JSON array of event objects
- Use the specified field names and formats (`YYYY-MM-DD` for date, `HH:MM` for time)

## Graph State

```
{
  "crawled_files": [str],              # paths to crawled markdown files
  "parsed_files": [str],               # paths to post_validation JSON files
  "errors": [str],                     # collected error messages
  "event_count": int                   # final count of events in output
}
```

## Logging

- All log output goes to `output/run.log` and stdout
- Log entries include: timestamp, stage, site/file, outcome (success/fail/retry), event counts

## Execution

```bash
python src/main.py
```

Reads `config.yaml`, builds the LangGraph graph, and runs it.
