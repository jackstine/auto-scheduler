"""LangGraph graph definition for the event scheduler pipeline."""

import asyncio
import logging
from typing import TypedDict

from langgraph.graph import StateGraph, START, END

from src.config import Config
from src.nodes.crawl import crawl
from src.nodes.parse import parse_all
from src.nodes.aggregate import aggregate
from src.nodes.filter_sort import filter_sort

logger = logging.getLogger(__name__)


class PipelineState(TypedDict):
    config: Config
    crawled_files: list[str]
    parsed_files: list[str]
    events: list[dict]
    errors: list[str]
    event_count: int


def crawl_node(state: PipelineState) -> dict:
    config = state["config"]
    crawled_files = crawl(config)
    return {"crawled_files": crawled_files}


def parse_node(state: PipelineState) -> dict:
    config = state["config"]
    parsed_files = asyncio.run(parse_all(state["crawled_files"], config))
    return {"parsed_files": parsed_files}


def aggregate_node(state: PipelineState) -> dict:
    events = aggregate(state["parsed_files"])
    return {"events": events}


def filter_sort_node(state: PipelineState) -> dict:
    config = state["config"]
    event_count = filter_sort(state["events"], config.output_dir)
    return {"event_count": event_count}


def build_graph() -> StateGraph:
    graph = StateGraph(PipelineState)

    graph.add_node("crawl", crawl_node)
    graph.add_node("parse", parse_node)
    graph.add_node("aggregate", aggregate_node)
    graph.add_node("filter_sort", filter_sort_node)

    graph.add_edge(START, "crawl")
    graph.add_edge("crawl", "parse")
    graph.add_edge("parse", "aggregate")
    graph.add_edge("aggregate", "filter_sort")
    graph.add_edge("filter_sort", END)

    return graph.compile()
