"""Unit tests for main entry point argument parsing."""

from src.main import parse_args


def test_parse_args_default():
    args = parse_args([])
    assert args.skip_crawl is False


def test_parse_args_skip_crawl():
    args = parse_args(["--skip-crawl"])
    assert args.skip_crawl is True
