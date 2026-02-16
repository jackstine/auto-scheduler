"""Entry point for the event scheduler pipeline."""

import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from src.config import load_config
from src.graph import build_graph


def setup_logging(output_dir: str) -> None:
    """Configure logging to stdout and run.log."""
    log_dir = Path(output_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    handlers = [
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_dir / "run.log", mode="w"),
    ]

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=handlers,
    )


def main():
    config = load_config()
    setup_logging(config.output_dir)

    logger = logging.getLogger(__name__)
    logger.info("Starting event scheduler pipeline")

    graph = build_graph()
    result = graph.invoke({
        "config": config,
        "crawled_files": [],
        "parsed_files": [],
        "events": [],
        "errors": [],
        "event_count": 0,
    })

    logger.info(f"Pipeline complete. {result['event_count']} events in output.")


if __name__ == "__main__":
    main()
