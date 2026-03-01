"""Unit tests for crawl node skip_crawl behavior."""

from pathlib import Path

from src.config import Config
from src.nodes.crawl import crawl, skip_crawl


def test_skip_crawl_returns_existing_files(tmp_path):
    """skip_crawl returns list of existing .md files in crawled dir."""
    output_dir = tmp_path / "output"
    crawled_dir = output_dir / "crawled"
    crawled_dir.mkdir(parents=True)
    (crawled_dir / "site_a.md").write_text("# Site A")
    (crawled_dir / "site_b.md").write_text("# Site B")

    config = Config(output_dir=str(output_dir), skip_crawl=True)
    result = skip_crawl(config)

    assert len(result) == 2
    assert all(f.endswith(".md") for f in result)


def test_skip_crawl_preserves_crawled_files(tmp_path):
    """skip_crawl must not delete existing crawled files."""
    output_dir = tmp_path / "output"
    crawled_dir = output_dir / "crawled"
    crawled_dir.mkdir(parents=True)
    md_file = crawled_dir / "site_a.md"
    md_file.write_text("# Site A content")

    config = Config(output_dir=str(output_dir), skip_crawl=True)
    skip_crawl(config)

    assert md_file.exists()
    assert md_file.read_text() == "# Site A content"


def test_skip_crawl_resets_parsed_dirs(tmp_path):
    """skip_crawl resets parsed subdirectories."""
    output_dir = tmp_path / "output"
    crawled_dir = output_dir / "crawled"
    crawled_dir.mkdir(parents=True)
    (crawled_dir / "site.md").write_text("content")

    # Create old parsed files that should be cleared
    pre_val = output_dir / "parsed" / "pre_validation"
    post_val = output_dir / "parsed" / "post_validation"
    pre_val.mkdir(parents=True)
    post_val.mkdir(parents=True)
    (pre_val / "old.json").write_text("[]")
    (post_val / "old.json").write_text("[]")

    config = Config(output_dir=str(output_dir), skip_crawl=True)
    skip_crawl(config)

    assert pre_val.exists()
    assert post_val.exists()
    assert not (pre_val / "old.json").exists()
    assert not (post_val / "old.json").exists()


def test_skip_crawl_empty_crawled_dir(tmp_path):
    """skip_crawl returns empty list when crawled dir is empty."""
    output_dir = tmp_path / "output"
    crawled_dir = output_dir / "crawled"
    crawled_dir.mkdir(parents=True)

    config = Config(output_dir=str(output_dir), skip_crawl=True)
    result = skip_crawl(config)

    assert result == []


def test_skip_crawl_missing_crawled_dir(tmp_path):
    """skip_crawl returns empty list when crawled dir doesn't exist."""
    output_dir = tmp_path / "output"

    config = Config(output_dir=str(output_dir), skip_crawl=True)
    result = skip_crawl(config)

    assert result == []


def test_crawl_with_skip_flag_delegates(tmp_path):
    """crawl() delegates to skip_crawl when config.skip_crawl is True."""
    output_dir = tmp_path / "output"
    crawled_dir = output_dir / "crawled"
    crawled_dir.mkdir(parents=True)
    (crawled_dir / "test.md").write_text("# Test")

    config = Config(output_dir=str(output_dir), skip_crawl=True)
    result = crawl(config)

    assert len(result) == 1
    assert result[0].endswith("test.md")


def test_skip_crawl_ignores_non_md_files(tmp_path):
    """skip_crawl only returns .md files, ignores others."""
    output_dir = tmp_path / "output"
    crawled_dir = output_dir / "crawled"
    crawled_dir.mkdir(parents=True)
    (crawled_dir / "site.md").write_text("# Site")
    (crawled_dir / "notes.txt").write_text("notes")
    (crawled_dir / "data.json").write_text("{}")

    config = Config(output_dir=str(output_dir), skip_crawl=True)
    result = skip_crawl(config)

    assert len(result) == 1
    assert result[0].endswith("site.md")
