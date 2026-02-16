"""Unit tests for utility functions."""

from src.utils import url_to_filename, filename_to_url


def test_url_to_filename():
    assert url_to_filename("https://www.meetup.com/austin-langchain-ai-group/") == "www.meetup.com_austin-langchain-ai-group"


def test_url_to_filename_no_trailing_slash():
    assert url_to_filename("https://aimug.org/events") == "aimug.org_events"


def test_filename_to_url():
    url = filename_to_url("www.meetup.com_austin-langchain-ai-group")
    assert url == "https://www.meetup.com/austin-langchain-ai-group"


def test_filename_to_url_from_md():
    url = filename_to_url("aimug.org_events.md")
    assert url == "https://aimug.org/events"
