"""Load application configuration from config.yaml."""

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class Config:
    links_file: str = "links.txt"
    output_dir: str = "output"
    max_sites: int = 0
    max_retries: int = 3
    max_concurrent_agents: int = 3
    model: str = "openrouter/aurora-alpha"
    crwl_command: str = "crwl"
    crwl_pyenv_version: str = "3.13.1"


def load_config(path: str = "config.yaml") -> Config:
    config_path = Path(path)
    if config_path.exists():
        with open(config_path) as f:
            data = yaml.safe_load(f) or {}
        return Config(**{k: v for k, v in data.items() if k in Config.__dataclass_fields__})
    return Config()
