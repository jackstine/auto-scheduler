"""Unit tests for config loading."""

from pathlib import Path

from src.config import Config, load_config


def test_defaults():
    config = Config()
    assert config.max_sites == 0
    assert config.max_retries == 3
    assert config.model == "openrouter/aurora-alpha"


def test_load_from_yaml(tmp_path):
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text("max_sites: 5\nmax_retries: 1\n")
    config = load_config(str(cfg_file))
    assert config.max_sites == 5
    assert config.max_retries == 1
    # Defaults for unset fields
    assert config.model == "openrouter/aurora-alpha"


def test_load_missing_file():
    config = load_config("nonexistent.yaml")
    assert config.max_sites == 0


def test_ignores_unknown_keys(tmp_path):
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text("max_sites: 2\nbogus_key: hello\n")
    config = load_config(str(cfg_file))
    assert config.max_sites == 2
    assert not hasattr(config, "bogus_key")
