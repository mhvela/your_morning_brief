"""Source seeding functionality for RSS feeds."""

import json
from typing import Any

from pydantic import BaseModel, ValidationError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.session import SessionLocal
from app.models.source import Source

logger = get_logger(__name__)


class SourceSeedModel(BaseModel):
    """Pydantic model for validating source seed data."""

    name: str
    url: str
    feed_url: str
    credibility_score: float | None = 0.5
    is_active: bool | None = True


def seed_sources(sources_data: list[dict[str, Any]]) -> dict[str, int]:
    """
    Seed sources from list of dictionaries.

    Args:
        sources_data: List of source dictionaries to seed

    Returns:
        Dictionary with counts of created, updated, and skipped sources

    Raises:
        ValueError: If source data is invalid
        Exception: If database operation fails
    """
    result = {"created": 0, "updated": 0, "skipped": 0}

    if not sources_data:
        logger.info("No sources provided for seeding")
        return result

    # Validate all sources first
    validated_sources = []
    for i, source_data in enumerate(sources_data):
        try:
            validated_source = SourceSeedModel(**source_data)
            validated_sources.append(validated_source)
        except ValidationError as e:
            raise ValueError(f"Invalid source data at index {i}: {e}") from e

    # Process sources in database
    with SessionLocal() as db:
        try:
            for validated_source in validated_sources:
                # Check if source exists by feed_url (unique constraint)
                existing_source = (
                    db.query(Source)
                    .filter_by(feed_url=validated_source.feed_url)
                    .first()
                )

                if existing_source:
                    # Update existing source
                    existing_source.name = validated_source.name
                    existing_source.url = validated_source.url
                    existing_source.credibility_score = (
                        validated_source.credibility_score or 0.5
                    )
                    existing_source.is_active = (
                        validated_source.is_active
                        if validated_source.is_active is not None
                        else True
                    )
                    result["updated"] += 1
                    logger.info(
                        "Updated source",
                        extra={
                            "source_id": existing_source.id,
                            "name": validated_source.name,
                            "feed_url": validated_source.feed_url,
                        },
                    )
                else:
                    # Create new source
                    new_source = Source(
                        name=validated_source.name,
                        url=validated_source.url,
                        feed_url=validated_source.feed_url,
                        credibility_score=validated_source.credibility_score,
                        is_active=validated_source.is_active,
                    )
                    db.add(new_source)
                    result["created"] += 1
                    logger.info(
                        "Created new source",
                        extra={
                            "name": validated_source.name,
                            "feed_url": validated_source.feed_url,
                        },
                    )

            # Commit all changes
            db.commit()

        except SQLAlchemyError as e:
            db.rollback()
            logger.error(
                "Database error during source seeding", extra={"error": str(e)}
            )
            raise
        except Exception as e:
            db.rollback()
            logger.error(
                "Unexpected error during source seeding", extra={"error": str(e)}
            )
            raise

    logger.info(
        "Source seeding completed",
        extra={
            "created": result["created"],
            "updated": result["updated"],
            "skipped": result["skipped"],
        },
    )

    return result


def seed_sources_from_file(file_path: str) -> dict[str, int]:
    """
    Seed sources from JSON file.

    Args:
        file_path: Path to JSON file containing source data

    Returns:
        Dictionary with counts of created, updated, and skipped sources

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If JSON is invalid or source data is malformed
        Exception: If database operation fails
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            sources_data = json.load(f)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Source seed file not found: {file_path}") from e
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in source seed file: {e}") from e

    if not isinstance(sources_data, list):
        raise ValueError("Source seed file must contain a JSON array")

    logger.info(
        "Loading sources from file",
        extra={"file_path": file_path, "source_count": len(sources_data)},
    )

    return seed_sources(sources_data)


def validate_source_data(source_data: dict[str, Any]) -> None:
    """
    Validate individual source data.

    Args:
        source_data: Dictionary containing source data

    Raises:
        ValueError: If required fields are missing or invalid
    """
    required_fields = ["name", "url", "feed_url"]

    for field in required_fields:
        if field not in source_data:
            raise ValueError(f"Missing required field: {field}")

        if not isinstance(source_data[field], str) or not source_data[field].strip():
            raise ValueError(f"Field '{field}' must be a non-empty string")

    # Validate optional fields
    if "credibility_score" in source_data:
        score = source_data["credibility_score"]
        if not isinstance(score, int | float) or not (0.0 <= score <= 1.0):
            raise ValueError("credibility_score must be a number between 0.0 and 1.0")

    if "is_active" in source_data and not isinstance(source_data["is_active"], bool):
        raise ValueError("is_active must be a boolean")


def get_source_by_feed_url(feed_url: str, db: Session) -> Source | None:
    """
    Get source by feed URL.

    Args:
        feed_url: Feed URL to search for
        db: Database session

    Returns:
        Source if found, None otherwise
    """
    return db.query(Source).filter_by(feed_url=feed_url).first()


def get_source_by_id(source_id: int, db: Session) -> Source | None:
    """
    Get source by ID.

    Args:
        source_id: Source ID to search for
        db: Database session

    Returns:
        Source if found, None otherwise
    """
    return db.query(Source).filter_by(id=source_id).first()


def get_or_create_source(feed_url: str, name: str | None = None) -> Source:
    """
    Get existing source or create inactive placeholder.

    Args:
        feed_url: Feed URL to search for or create
        name: Optional name for new source

    Returns:
        Source instance (existing or newly created)
    """
    with SessionLocal() as db:
        # Try to find existing source
        existing_source = get_source_by_feed_url(feed_url, db)
        if existing_source:
            return existing_source

        # Create inactive placeholder
        placeholder_name = name or f"Unknown Source ({feed_url})"
        new_source = Source(
            name=placeholder_name,
            url=feed_url,  # Use feed_url as fallback for url
            feed_url=feed_url,
            credibility_score=0.5,
            is_active=False,  # Inactive until properly configured
        )

        try:
            db.add(new_source)
            db.commit()
            db.refresh(new_source)

            logger.info(
                "Created placeholder source",
                extra={
                    "source_id": new_source.id,
                    "name": placeholder_name,
                    "feed_url": feed_url,
                },
            )

            return new_source

        except SQLAlchemyError as e:
            db.rollback()
            logger.error("Failed to create placeholder source", extra={"error": str(e)})
            raise
