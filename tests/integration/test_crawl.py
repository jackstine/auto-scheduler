"""Integration test: crawl a single site."""

from pathlib import Path

from src.config import Config
from src.nodes.crawl import crawl


def test_crawl_single_site(tmp_path):
    # Create a links file with one URL
    links = tmp_path / "links.txt"
    links.write_text("https://aimug.org/events\n")

    config = Config(
        links_file=str(links),
        output_dir=str(tmp_path / "output"),
        max_sites=1,
    )

    crawled = crawl(config)
    assert len(crawled) == 1
    content = Path(crawled[0]).read_text()
    assert len(content) > 0
