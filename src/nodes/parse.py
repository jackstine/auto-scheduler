"""Parse node: runs LLM agents in parallel to extract events from crawled markdown."""

import asyncio
import json
import logging
import os
from datetime import date
from pathlib import Path

from langchain_openai import ChatOpenAI

from src.config import Config
from src.nodes.validate import validate_response

logger = logging.getLogger(__name__)


def _build_prompt(markdown_content: str) -> str:
    """Load prompt template and inject content."""
    template = Path("prompts/parse_schedule.md").read_text()
    return template.replace("{today_date}", date.today().isoformat()).replace("{content}", markdown_content)


async def _parse_single(llm: ChatOpenAI, filepath: str, config: Config) -> list[dict]:
    """Parse a single crawled file with retry logic."""
    output_dir = Path(config.output_dir)
    filename = Path(filepath).stem + ".json"
    pre_val_path = output_dir / "parsed" / "pre_validation" / filename
    post_val_path = output_dir / "parsed" / "post_validation" / filename

    markdown_content = Path(filepath).read_text()
    prompt = _build_prompt(markdown_content)

    for attempt in range(1, config.max_retries + 1):
        try:
            logger.info(f"Parsing {Path(filepath).name} (attempt {attempt}/{config.max_retries})")
            response = await llm.ainvoke(prompt)
            raw = response.content

            # Save pre-validation
            pre_val_path.write_text(raw)

            valid_objects, error = validate_response(raw)
            if valid_objects is None:
                logger.warning(f"Validation failed for {Path(filepath).name}: {error}")
                continue

            # Save post-validation
            post_val_path.write_text(json.dumps(valid_objects, indent=2))
            logger.info(f"Extracted {len(valid_objects)} events from {Path(filepath).name}")
            return valid_objects

        except Exception as e:
            logger.error(f"Agent error for {Path(filepath).name} (attempt {attempt}): {e}")
            continue

    logger.error(f"All {config.max_retries} attempts failed for {Path(filepath).name}")
    # Write empty array to post_validation so downstream knows it was processed
    post_val_path.write_text("[]")
    return []


async def parse_all(crawled_files: list[str], config: Config) -> list[str]:
    """Parse all crawled files in parallel, return list of post_validation file paths."""
    llm = ChatOpenAI(
        model=config.model,
        openai_api_key=os.environ["OPENROUTER_API_KEY"],
        openai_api_base="https://openrouter.ai/api/v1",
    )

    semaphore = asyncio.Semaphore(config.max_concurrent_agents)

    async def limited(filepath: str):
        async with semaphore:
            return await _parse_single(llm, filepath, config)

    await asyncio.gather(*[limited(f) for f in crawled_files])

    # Return post_validation file paths
    post_val_dir = Path(config.output_dir) / "parsed" / "post_validation"
    return [str(p) for p in post_val_dir.glob("*.json")]
