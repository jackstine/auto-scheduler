"""Integration test: parse one crawled file via LLM agent."""

import asyncio
import json
import shutil
from pathlib import Path

import pytest
from dotenv import load_dotenv

load_dotenv()

from src.config import Config
from src.nodes.parse import parse_all

TEST_OUTPUT_DIR = Path("tests/output/test_parse_agent")


@pytest.mark.llm
def test_parse_single_file():
    # Clean and set up directory structure
    if TEST_OUTPUT_DIR.exists():
        shutil.rmtree(TEST_OUTPUT_DIR)
    for subdir in ["crawled", "parsed/pre_validation", "parsed/post_validation"]:
        (TEST_OUTPUT_DIR / subdir).mkdir(parents=True)

    # Use existing crawled content or a small sample
    crawled_file = TEST_OUTPUT_DIR / "crawled" / "aimug.org_events.md"
    sample = Path("crawled_output/https___aimug.org_events.md")
    if sample.exists():
        crawled_file.write_text(sample.read_text())
    else:
        pytest.skip("No sample crawled file available")

    config = Config(
        output_dir=str(TEST_OUTPUT_DIR),
        max_retries=2,
    )

    parsed = asyncio.run(parse_all([str(crawled_file)], config))

    assert len(parsed) >= 1
    data = json.loads(Path(parsed[0]).read_text())
    assert isinstance(data, list)
