"""CLI command for RSS feed ingestion."""

import argparse
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.session import SessionLocal
from app.ingestion.feed_client import FeedClient
from app.ingestion.mapper import ArticleMapper, validate_article_data
from app.ingestion.seeder import (
    get_or_create_source,
    get_source_by_id,
    seed_sources_from_file,
)
from app.models.article import Article
from app.models.source import Source

logger = get_logger(__name__)


def _get_source_for_ingestion(feed_url: str, source_id: int | None) -> Source:
    """Get or create source for ingestion."""
    if source_id:
        with SessionLocal() as db:
            source = get_source_by_id(source_id, db)
            if not source:
                raise ValueError(f"Source with ID {source_id} not found")
    else:
        source = get_or_create_source(feed_url)
    return source


def _process_feed_entry(
    entry: Any, source_id: int, mapper: ArticleMapper, db: Session
) -> str:
    """Process a single feed entry and return result status."""
    # Map entry to article data
    article_data = mapper.map_entry_to_article(entry, source_id)

    # Validate article data
    validate_article_data(article_data)

    # Check if article already exists (by content_hash)
    existing_article = (
        db.query(Article).filter_by(content_hash=article_data["content_hash"]).first()
    )

    if existing_article:
        logger.debug(
            "Skipping duplicate article",
            extra={"content_hash": article_data["content_hash"][:16] + "..."},
        )
        return "skipped"

    # Create new article
    article = Article(**article_data)
    db.add(article)

    logger.debug(
        "Inserted article",
        extra={
            "title": (
                article_data["title"][:50] + "..."
                if len(article_data["title"]) > 50
                else article_data["title"]
            ),
            "content_hash": article_data["content_hash"][:16] + "...",
        },
    )
    return "inserted"


def _update_source_after_ingestion(
    source: Source, success: bool, error: str | None
) -> None:
    """Update source metadata after ingestion."""
    try:
        with SessionLocal() as db:
            if success:
                source.last_fetched_at = datetime.now(UTC)
                source.error_count = 0
                source.last_error = None
            else:
                source.error_count += 1
                source.last_error = str(error)[:1000] if error else None
            db.commit()
    except Exception:
        pass  # Don't let error logging fail the whole operation


def ingest_feed_from_url(feed_url: str, source_id: int | None = None) -> dict[str, int]:
    """
    Ingest articles from a feed URL.

    Args:
        feed_url: URL of the RSS feed to ingest
        source_id: Optional source ID to associate with articles

    Returns:
        Dictionary with ingestion statistics
    """
    result = {"parsed": 0, "inserted": 0, "skipped": 0, "errors": 0}
    start_time = time.time()
    source = None

    try:
        # Get or create source
        source = _get_source_for_ingestion(feed_url, source_id)

        logger.info(
            "Starting feed ingestion",
            extra={
                "feed_url": feed_url,
                "source_id": source.id,
                "source_name": source.name,
            },
        )

        # Fetch and parse feed
        client: FeedClient = FeedClient()
        feed = client.fetch_feed(feed_url)

        if not hasattr(feed, "entries") or not feed.entries:
            logger.warning("Feed contains no entries", extra={"feed_url": feed_url})
            return result

        result["parsed"] = len(feed.entries)

        # Process entries
        mapper = ArticleMapper()
        with SessionLocal() as db:
            for entry in feed.entries:
                try:
                    status = _process_feed_entry(entry, source.id, mapper, db)
                    result[status] += 1

                except Exception as e:
                    result["errors"] += 1
                    logger.warning(
                        "Failed to process article",
                        extra={
                            "error": str(e),
                            "entry_title": getattr(entry, "title", "Unknown"),
                        },
                    )

            # Commit all changes
            try:
                db.commit()
                _update_source_after_ingestion(source, True, None)

            except SQLAlchemyError as e:
                db.rollback()
                logger.error("Database commit failed", extra={"error": str(e)})
                result["errors"] += result["inserted"]
                result["inserted"] = 0
                raise

    except Exception as e:
        result["errors"] += 1
        logger.error(
            "Feed ingestion failed", extra={"feed_url": feed_url, "error": str(e)}
        )

        # Update source error count
        if source:
            _update_source_after_ingestion(source, False, str(e))

    finally:
        duration = time.time() - start_time
        logger.info(
            "Feed ingestion completed",
            extra={
                "feed_url": feed_url,
                "duration_sec": round(duration, 2),
                "parsed": result["parsed"],
                "inserted": result["inserted"],
                "skipped": result["skipped"],
                "errors": result["errors"],
            },
        )

    return result


def ingest_feed_from_file(file_path: str) -> dict[str, int]:
    """
    Ingest articles from a local RSS file (for testing).

    Args:
        file_path: Path to local RSS file

    Returns:
        Dictionary with ingestion statistics
    """
    result = {"parsed": 0, "inserted": 0, "skipped": 0, "errors": 0}

    try:
        # Read file content
        with open(file_path, "rb") as f:
            content = f.read()

        # Create a mock source for file ingestion
        source = get_or_create_source(
            f"file://{file_path}", f"Local File ({Path(file_path).name})"
        )

        logger.info(
            "Starting file ingestion",
            extra={"file_path": file_path, "source_id": source.id},
        )

        # Parse feed content directly
        import feedparser

        feed = feedparser.parse(content)

        if not hasattr(feed, "entries") or not feed.entries:
            logger.warning("File contains no entries", extra={"file_path": file_path})
            return result

        result["parsed"] = len(feed.entries)

        # Process entries (same logic as URL ingestion)
        mapper = ArticleMapper()
        with SessionLocal() as db:
            for entry in feed.entries:
                try:
                    # Map entry to article data
                    article_data = mapper.map_entry_to_article(entry, source.id)

                    # Validate article data
                    validate_article_data(article_data)

                    # Check if article already exists
                    existing_article = (
                        db.query(Article)
                        .filter_by(content_hash=article_data["content_hash"])
                        .first()
                    )

                    if existing_article:
                        result["skipped"] += 1
                        continue

                    # Create new article
                    article = Article(**article_data)
                    db.add(article)
                    result["inserted"] += 1

                except Exception as e:
                    result["errors"] += 1
                    logger.warning(
                        "Failed to process article from file",
                        extra={
                            "error": str(e),
                            "entry_title": getattr(entry, "title", "Unknown"),
                        },
                    )

            # Commit all changes
            try:
                db.commit()
            except SQLAlchemyError as e:
                db.rollback()
                logger.error(
                    "Database commit failed for file ingestion", extra={"error": str(e)}
                )
                result["errors"] += result["inserted"]
                result["inserted"] = 0
                raise

    except Exception as e:
        result["errors"] += 1
        logger.error(
            "File ingestion failed", extra={"file_path": file_path, "error": str(e)}
        )

    logger.info(
        "File ingestion completed",
        extra={
            "file_path": file_path,
            "parsed": result["parsed"],
            "inserted": result["inserted"],
            "skipped": result["skipped"],
            "errors": result["errors"],
        },
    )

    return result


def create_argument_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Ingest RSS feeds into Your Morning Brief database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Seed sources from JSON file
  python -m app.ingestion.ingest_one --seed-sources app/data/sources.seed.json

  # Ingest feed by URL
  python -m app.ingestion.ingest_one --feed-url https://techcrunch.com/feed/

  # Ingest feed by source ID
  python -m app.ingestion.ingest_one --source-id 1

  # Ingest from local file (for testing)
  python -m app.ingestion.ingest_one --file tests/fixtures/feeds/sample_feed.xml
        """,
    )

    # Mutually exclusive group for different operations
    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument(
        "--seed-sources",
        type=str,
        metavar="JSON_FILE",
        help="Seed sources from JSON file",
    )

    group.add_argument(
        "--feed-url", type=str, metavar="URL", help="Ingest articles from feed URL"
    )

    group.add_argument(
        "--source-id", type=int, metavar="ID", help="Ingest articles from source by ID"
    )

    group.add_argument(
        "--file",
        type=str,
        metavar="FILE_PATH",
        help="Ingest articles from local RSS file (for testing)",
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    return parser


def _handle_seed_sources(args: argparse.Namespace) -> int:
    """Handle source seeding operation."""
    if not Path(args.seed_sources).exists():
        logger.error(f"Source file not found: {args.seed_sources}")
        return 1

    result = seed_sources_from_file(args.seed_sources)
    print(
        f"Source seeding completed: {result['created']} created, "
        f"{result['updated']} updated, {result['skipped']} skipped"
    )
    return 0


def _handle_feed_url(args: argparse.Namespace) -> int:
    """Handle feed URL ingestion."""
    result = ingest_feed_from_url(args.feed_url)
    print(
        f"Feed ingestion completed: {result['parsed']} parsed, "
        f"{result['inserted']} inserted, {result['skipped']} skipped, "
        f"{result['errors']} errors"
    )
    return 0


def _handle_source_id(args: argparse.Namespace) -> int:
    """Handle source ID ingestion."""
    with SessionLocal() as db:
        source = get_source_by_id(args.source_id, db)
        if not source:
            logger.error(f"Source with ID {args.source_id} not found")
            return 1

    result = ingest_feed_from_url(source.feed_url, args.source_id)
    print(
        f"Feed ingestion completed: {result['parsed']} parsed, "
        f"{result['inserted']} inserted, {result['skipped']} skipped, "
        f"{result['errors']} errors"
    )
    return 0


def _handle_file_ingestion(args: argparse.Namespace) -> int:
    """Handle file ingestion."""
    if not Path(args.file).exists():
        logger.error(f"Feed file not found: {args.file}")
        return 1

    result = ingest_feed_from_file(args.file)
    print(
        f"File ingestion completed: {result['parsed']} parsed, "
        f"{result['inserted']} inserted, {result['skipped']} skipped, "
        f"{result['errors']} errors"
    )
    return 0


def main() -> int:
    """Main CLI entry point."""
    parser = create_argument_parser()
    args = parser.parse_args()

    # Configure logging level
    if args.verbose:
        import logging

        logging.getLogger("app").setLevel(logging.DEBUG)

    try:
        if args.seed_sources:
            return _handle_seed_sources(args)
        elif args.feed_url:
            return _handle_feed_url(args)
        elif args.source_id:
            return _handle_source_id(args)
        elif args.file:
            return _handle_file_ingestion(args)

        return 0

    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        return 130

    except Exception as e:
        logger.error(f"Operation failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
