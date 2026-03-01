"""Unit tests for crawl node: skip_crawl and concurrent crawling."""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

import pytest

from src.config import Config
from src.nodes.crawl import crawl, skip_crawl, _crawl_single, _crawl_all_async


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


# --- Concurrent crawling tests ---


@pytest.mark.asyncio
async def test_crawl_single_success(tmp_path):
    """_crawl_single writes output and returns filepath on success."""
    filepath = tmp_path / "output" / "crawled" / "test.md"
    filepath.parent.mkdir(parents=True)
    config = Config(output_dir=str(tmp_path / "output"), crwl_command="echo")

    mock_proc = AsyncMock()
    mock_proc.communicate = AsyncMock(return_value=(b"# Page content", b""))
    mock_proc.returncode = 0

    with patch("src.nodes.crawl.asyncio.create_subprocess_exec", return_value=mock_proc):
        result = await _crawl_single("https://example.com", filepath, config)

    assert result == str(filepath)
    assert filepath.read_text() == "# Page content"


@pytest.mark.asyncio
async def test_crawl_single_failure_returns_none(tmp_path):
    """_crawl_single returns None when process returns non-zero."""
    filepath = tmp_path / "output" / "crawled" / "fail.md"
    filepath.parent.mkdir(parents=True)
    config = Config(output_dir=str(tmp_path / "output"))

    mock_proc = AsyncMock()
    mock_proc.communicate = AsyncMock(return_value=(b"", b"error occurred"))
    mock_proc.returncode = 1

    with patch("src.nodes.crawl.asyncio.create_subprocess_exec", return_value=mock_proc):
        result = await _crawl_single("https://example.com/fail", filepath, config)

    assert result is None
    assert not filepath.exists()


@pytest.mark.asyncio
async def test_crawl_single_timeout_returns_none(tmp_path):
    """_crawl_single returns None on timeout."""
    filepath = tmp_path / "output" / "crawled" / "timeout.md"
    filepath.parent.mkdir(parents=True)
    config = Config(output_dir=str(tmp_path / "output"))

    mock_proc = AsyncMock()
    mock_proc.communicate = AsyncMock(side_effect=asyncio.TimeoutError)

    with patch("src.nodes.crawl.asyncio.create_subprocess_exec", return_value=mock_proc):
        with patch("src.nodes.crawl.asyncio.wait_for", side_effect=asyncio.TimeoutError):
            result = await _crawl_single("https://slow.example.com", filepath, config)

    assert result is None


@pytest.mark.asyncio
async def test_crawl_all_async_concurrent(tmp_path):
    """_crawl_all_async runs multiple crawls concurrently."""
    output_dir = tmp_path / "output"
    (output_dir / "crawled").mkdir(parents=True)

    config = Config(
        output_dir=str(output_dir),
        max_concurrent_crawls=3,
    )
    urls = ["https://a.com", "https://b.com", "https://c.com"]

    call_count = 0

    async def mock_create_subprocess(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        proc = AsyncMock()
        proc.communicate = AsyncMock(return_value=(b"# Content", b""))
        proc.returncode = 0
        return proc

    with patch("src.nodes.crawl.asyncio.create_subprocess_exec", side_effect=mock_create_subprocess):
        results = await _crawl_all_async(urls, config, output_dir)

    assert len(results) == 3
    assert call_count == 3
    # All files should exist
    for r in results:
        assert Path(r).exists()


@pytest.mark.asyncio
async def test_crawl_all_async_filters_failures(tmp_path):
    """_crawl_all_async filters out failed crawls from results."""
    output_dir = tmp_path / "output"
    (output_dir / "crawled").mkdir(parents=True)

    config = Config(
        output_dir=str(output_dir),
        max_concurrent_crawls=5,
    )
    urls = ["https://good.com", "https://bad.com"]

    async def mock_create_subprocess(*args, **kwargs):
        proc = AsyncMock()
        url = args[2]  # crwl_command, "crawl", url, "-o", "markdown"
        if "bad" in url:
            proc.communicate = AsyncMock(return_value=(b"", b"error"))
            proc.returncode = 1
        else:
            proc.communicate = AsyncMock(return_value=(b"# Good", b""))
            proc.returncode = 0
        return proc

    with patch("src.nodes.crawl.asyncio.create_subprocess_exec", side_effect=mock_create_subprocess):
        results = await _crawl_all_async(urls, config, output_dir)

    assert len(results) == 1
    assert "good.com" in results[0]


@pytest.mark.asyncio
async def test_crawl_all_async_respects_semaphore(tmp_path):
    """_crawl_all_async respects max_concurrent_crawls semaphore."""
    output_dir = tmp_path / "output"
    (output_dir / "crawled").mkdir(parents=True)

    config = Config(
        output_dir=str(output_dir),
        max_concurrent_crawls=2,
    )
    urls = [f"https://site{i}.com" for i in range(5)]

    max_concurrent = 0
    current_concurrent = 0
    lock = asyncio.Lock()

    async def mock_create_subprocess(*args, **kwargs):
        nonlocal max_concurrent, current_concurrent
        async with lock:
            current_concurrent += 1
            if current_concurrent > max_concurrent:
                max_concurrent = current_concurrent

        # Simulate some work
        await asyncio.sleep(0.01)

        async with lock:
            current_concurrent -= 1

        proc = AsyncMock()
        proc.communicate = AsyncMock(return_value=(b"# Content", b""))
        proc.returncode = 0
        return proc

    with patch("src.nodes.crawl.asyncio.create_subprocess_exec", side_effect=mock_create_subprocess):
        results = await _crawl_all_async(urls, config, output_dir)

    assert len(results) == 5
    assert max_concurrent <= 2


def test_crawl_concurrent_with_links_file(tmp_path):
    """crawl() reads links file and crawls concurrently."""
    output_dir = tmp_path / "output"
    links = tmp_path / "links.txt"
    links.write_text("https://a.com\nhttps://b.com\n")

    config = Config(
        links_file=str(links),
        output_dir=str(output_dir),
        max_concurrent_crawls=2,
    )

    async def mock_create_subprocess(*args, **kwargs):
        proc = AsyncMock()
        proc.communicate = AsyncMock(return_value=(b"# Content", b""))
        proc.returncode = 0
        return proc

    with patch("src.nodes.crawl.asyncio.create_subprocess_exec", side_effect=mock_create_subprocess):
        results = crawl(config)

    assert len(results) == 2


def test_crawl_missing_links_file(tmp_path):
    """crawl() returns empty list when links file doesn't exist."""
    config = Config(
        links_file=str(tmp_path / "missing.txt"),
        output_dir=str(tmp_path / "output"),
    )
    result = crawl(config)
    assert result == []


def test_crawl_deduplicates_urls(tmp_path):
    """crawl() deduplicates URLs from links file."""
    output_dir = tmp_path / "output"
    links = tmp_path / "links.txt"
    links.write_text("https://a.com\nhttps://a.com\nhttps://b.com\n")

    config = Config(
        links_file=str(links),
        output_dir=str(output_dir),
        max_concurrent_crawls=5,
    )

    call_urls = []

    async def mock_create_subprocess(*args, **kwargs):
        call_urls.append(args[2])
        proc = AsyncMock()
        proc.communicate = AsyncMock(return_value=(b"# Content", b""))
        proc.returncode = 0
        return proc

    with patch("src.nodes.crawl.asyncio.create_subprocess_exec", side_effect=mock_create_subprocess):
        results = crawl(config)

    assert len(results) == 2
    assert len(call_urls) == 2


def test_crawl_respects_max_sites(tmp_path):
    """crawl() limits URLs to max_sites."""
    output_dir = tmp_path / "output"
    links = tmp_path / "links.txt"
    links.write_text("https://a.com\nhttps://b.com\nhttps://c.com\n")

    config = Config(
        links_file=str(links),
        output_dir=str(output_dir),
        max_sites=2,
        max_concurrent_crawls=5,
    )

    async def mock_create_subprocess(*args, **kwargs):
        proc = AsyncMock()
        proc.communicate = AsyncMock(return_value=(b"# Content", b""))
        proc.returncode = 0
        return proc

    with patch("src.nodes.crawl.asyncio.create_subprocess_exec", side_effect=mock_create_subprocess):
        results = crawl(config)

    assert len(results) == 2
