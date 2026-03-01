"""Integration test: skip_crawl reuses existing crawled files end-to-end."""

import json
from pathlib import Path

from src.config import Config
from src.nodes.crawl import crawl


def test_skip_crawl_reuses_previously_crawled(tmp_path):
    """Full skip_crawl flow: pre-populate crawled dir, verify reuse."""
    output_dir = tmp_path / "output"
    crawled_dir = output_dir / "crawled"
    crawled_dir.mkdir(parents=True)

    # Simulate previously crawled content
    (crawled_dir / "aimug.org_events.md").write_text("# AIMUG Events\n- Event 1\n- Event 2")
    (crawled_dir / "asmbly.org.md").write_text("# Asmbly\n- Workshop A")

    # Pre-populate parsed dirs with stale data that should be cleared
    pre_val = output_dir / "parsed" / "pre_validation"
    post_val = output_dir / "parsed" / "post_validation"
    pre_val.mkdir(parents=True)
    post_val.mkdir(parents=True)
    (pre_val / "stale.json").write_text("[]")
    (post_val / "stale.json").write_text("[]")

    config = Config(
        output_dir=str(output_dir),
        skip_crawl=True,
    )

    result = crawl(config)

    # Should return both .md files
    assert len(result) == 2
    filenames = [Path(f).name for f in result]
    assert "aimug.org_events.md" in filenames
    assert "asmbly.org.md" in filenames

    # Original files should still exist with same content
    assert (crawled_dir / "aimug.org_events.md").read_text().startswith("# AIMUG")
    assert (crawled_dir / "asmbly.org.md").read_text().startswith("# Asmbly")

    # Stale parsed files should be cleaned
    assert not (pre_val / "stale.json").exists()
    assert not (post_val / "stale.json").exists()

    # Parsed directories should still exist (empty, ready for new run)
    assert pre_val.exists()
    assert post_val.exists()
