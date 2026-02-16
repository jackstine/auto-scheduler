# Configuration

All configuration is done via `config.yaml` in the project root.

## Example

```yaml
links_file: links.txt
output_dir: output
max_sites: 0
max_retries: 3
max_concurrent_agents: 3
model: openrouter/aurora-alpha
crwl_command: crwl
crwl_pyenv_version: "3.13.1"
```

## Settings

| Setting                | Type    | Default                  | Description                                                        |
|------------------------|---------|--------------------------|--------------------------------------------------------------------|
| `links_file`           | string  | `links.txt`              | Path to the file containing URLs to crawl, one per line.           |
| `output_dir`           | string  | `output`                 | Directory for all output (crawled markdown, parsed JSON, results). |
| `max_sites`            | integer | `0`                      | Max number of sites to crawl. `0` means crawl all.                 |
| `max_retries`          | integer | `3`                      | Number of times to retry an agent if validation fails.             |
| `max_concurrent_agents`| integer | `3`                      | Max number of LLM agents running in parallel.                      |
| `model`                | string  | `openrouter/aurora-alpha` | OpenRouter model identifier.                                      |
| `crwl_command`         | string  | `crwl`                   | CLI command used for crawling.                                     |
| `crwl_pyenv_version`   | string  | `3.13.1`                 | pyenv Python version to use when running the crawl command.        |

## Notes

- If `config.yaml` is missing, all defaults are used.
- Unknown keys in the YAML file are ignored.
- Set `max_sites` to a small number (e.g., `3`) for testing to save time and LLM costs.
- The `OPENROUTER_API_KEY` must be set in `.env` (loaded via dotenv).
