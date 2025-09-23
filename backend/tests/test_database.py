import hashlib
from collections.abc import Generator
from datetime import datetime

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.db.base import Base
from app.models.article import Article
from app.models.source import Source
from app.models.topic import Topic
from app.models.user import User


@pytest.fixture(scope="session")
def db_engine() -> Generator[Engine, None, None]:
    """Create test database engine"""
    # Use test database URL if available, otherwise use main database URL
    database_url = settings.test_database_url or settings.database_url
    assert database_url is not None
    engine = create_engine(database_url, echo=False, future=True)

    # Create all tables
    Base.metadata.create_all(bind=engine)
    yield engine

    # Clean up
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(db_engine: Engine) -> Generator[Session, None, None]:
    """Create a fresh database session for each test"""
    connection = db_engine.connect()
    transaction = connection.begin()
    SessionLocal = sessionmaker(bind=connection)  # noqa: N806
    session = SessionLocal()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


def test_database_connection(db_session: Session) -> None:
    """Test basic database connectivity"""
    result = db_session.execute(text("SELECT 1"))
    assert result.scalar() == 1


def test_user_creation(db_session: Session) -> None:
    """Test creating a user"""
    user = User(email="test@example.com", is_active=True)
    db_session.add(user)
    db_session.commit()

    assert user.id is not None
    assert user.created_at is not None
    assert user.updated_at is not None
    assert user.email == "test@example.com"
    assert user.is_active is True


def test_topic_with_keywords(db_session: Session) -> None:
    """Test creating a topic with keywords"""
    user = User(email="test@example.com")
    db_session.add(user)
    db_session.commit()

    topic = Topic(
        user_id=user.id,
        name="Technology",
        keywords=["AI", "machine learning", "robotics"],
    )
    db_session.add(topic)
    db_session.commit()

    assert topic.id is not None
    assert len(topic.keywords) == 3
    assert "AI" in topic.keywords
    assert topic.is_active is True


def test_source_creation(db_session: Session) -> None:
    """Test creating a news source"""
    source = Source(
        name="TechCrunch",
        url="https://techcrunch.com",
        feed_url="https://techcrunch.com/feed",
    )
    db_session.add(source)
    db_session.commit()

    assert source.id is not None
    assert source.credibility_score == 0.5  # default value
    assert source.is_active is True
    assert source.error_count == 0


def test_article_creation(db_session: Session) -> None:
    """Test creating an article"""
    source = Source(
        name="TechCrunch",
        url="https://techcrunch.com",
        feed_url="https://techcrunch.com/feed",
    )
    db_session.add(source)
    db_session.commit()

    content_hash = hashlib.sha256(b"unique_content").hexdigest()
    article = Article(
        source_id=source.id,
        title="Test Article",
        link="https://example.com/article",
        content_hash=content_hash,
        published_at=datetime.utcnow(),
        tags=["tech", "news"],
    )
    db_session.add(article)
    db_session.commit()

    assert article.id is not None
    assert len(article.tags) == 2
    assert "tech" in article.tags


def test_article_deduplication(db_session: Session) -> None:
    """Test article content hash uniqueness"""
    source = Source(
        name="TechCrunch",
        url="https://techcrunch.com",
        feed_url="https://techcrunch.com/feed",
    )
    db_session.add(source)
    db_session.commit()

    content_hash = hashlib.sha256(b"unique_content").hexdigest()

    # Create first article
    article1 = Article(
        source_id=source.id,
        title="Test Article",
        link="https://example.com/1",
        content_hash=content_hash,
        published_at=datetime.utcnow(),
    )
    db_session.add(article1)
    db_session.commit()

    # Try to add duplicate
    article2 = Article(
        source_id=source.id,
        title="Duplicate Article",
        link="https://example.com/2",
        content_hash=content_hash,  # Same hash
        published_at=datetime.utcnow(),
    )
    db_session.add(article2)

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_unique_email_constraint(db_session: Session) -> None:
    """Test that user emails must be unique"""
    user1 = User(email="test@example.com", is_active=True)
    db_session.add(user1)
    db_session.commit()

    user2 = User(email="test@example.com", is_active=True)
    db_session.add(user2)

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_foreign_key_constraint(db_session: Session) -> None:
    """Test foreign key constraint enforcement"""
    # Try to create a topic without a valid user
    topic = Topic(
        user_id=999, name="Test Topic", keywords=["test"]  # Non-existent user
    )
    db_session.add(topic)

    with pytest.raises(IntegrityError):
        db_session.commit()
