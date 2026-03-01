"""Crawl node: downloads site content as markdown using crwl CLI."""

import asyncio
import logging
import os
import shutil
from pathlib import Path

from src.config import Config
from src.utils import url_to_filename

logger = logging.getLogger(__name__)


def _setup_output_dirs(output_dir: Path) -> None:
    """Create output subdirectories for parsed results."""
    for subdir in ["crawled", "parsed/pre_validation", "parsed/post_validation"]:
        (output_dir / subdir).mkdir(parents=True, exist_ok=True)


def skip_crawl(config: Config) -> list[str]:
    """Skip crawling and return existing crawled files."""
    output_dir = Path(config.output_dir)
    crawled_dir = output_dir / "crawled"

    # Reset only parsed directories, preserve crawled files
    for subdir in ["parsed/pre_validation", "parsed/post_validation"]:
        target = output_dir / subdir
        if target.exists():
            shutil.rmtree(target)
        target.mkdir(parents=True, exist_ok=True)

    if not crawled_dir.exists() or not any(crawled_dir.iterdir()):
        logger.warning("skip_crawl enabled but no crawled files found in %s", crawled_dir)
        return []

    crawled_files = sorted(str(p) for p in crawled_dir.glob("*.md"))
    logger.info("skip_crawl: reusing %d existing crawled files", len(crawled_files))
    return crawled_files


async def _crawl_single(url: str, filepath: Path, config: Config) -> str | None:
    """Crawl a single URL asynchronously. Returns filepath on success, None on failure."""
    try:
        logger.info(f"Crawling: {url}")
        env = {**os.environ}
        if config.crwl_pyenv_version:
            env["PYENV_VERSION"] = config.crwl_pyenv_version

        proc = await asyncio.create_subprocess_exec(
            config.crwl_command, "crawl", url, "-o", "markdown",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=60)

        if proc.returncode != 0:
            logger.error(f"Crawl failed for {url}: {stderr.decode()}")
            return None

        filepath.write_text(stdout.decode())
        logger.info(f"Saved: {filepath}")
        return str(filepath)

    except asyncio.TimeoutError:
        logger.error(f"Crawl timed out for {url}")
        return None
    except Exception as e:
        logger.error(f"Crawl error for {url}: {e}")
        return None


async def _crawl_all_async(urls: list[str], config: Config, output_dir: Path) -> list[str]:
    """Crawl all URLs concurrently with a semaphore limit."""
    semaphore = asyncio.Semaphore(config.max_concurrent_crawls)

    async def limited(url: str, filepath: Path) -> str | None:
        async with semaphore:
            return await _crawl_single(url, filepath, config)

    tasks = []
    for url in urls:
        filename = url_to_filename(url) + ".md"
        filepath = output_dir / "crawled" / filename
        tasks.append(limited(url, filepath))

    results = await asyncio.gather(*tasks)
    return [r for r in results if r is not None]


def crawl(config: Config) -> list[str]:
    """Read links, crawl sites concurrently, return list of crawled file paths."""
    if config.skip_crawl:
        return skip_crawl(config)

    output_dir = Path(config.output_dir)

    # Clear output directory
    if output_dir.exists():
        shutil.rmtree(output_dir)
    _setup_output_dirs(output_dir)

    # Read and deduplicate URLs
    links_path = Path(config.links_file)
    if not links_path.exists():
        logger.error(f"Links file not found: {links_path}")
        return []

    urls = []
    seen = set()
    for line in links_path.read_text().splitlines():
        url = line.strip()
        if url and url not in seen:
            seen.add(url)
            urls.append(url)

    # Apply max_sites limit
    if config.max_sites > 0:
        urls = urls[: config.max_sites]

    logger.info(f"Crawling {len(urls)} sites concurrently (max {config.max_concurrent_crawls} parallel)")

    crawled_files = asyncio.run(_crawl_all_async(urls, config, output_dir))

    logger.info(f"Crawled {len(crawled_files)}/{len(urls)} sites successfully")
    return crawled_files
