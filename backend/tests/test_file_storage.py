import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from backend.app.core.config import settings
from backend.app.db.database import Base
from backend.app.services.file_storage_service import (
    DatabaseFileNotFoundError,
    FileStorageConfigurationError,
    delete_file_blob,
    get_file_blob,
    get_file_storage_backend,
    make_storage_key,
    put_file_blob,
    use_database_storage,
)
engine = create_engine(
    "sqlite://",
    connect_args={
        "check_same_thread": False,
    },
    poolclass=StaticPool,
)
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)
@pytest.fixture(autouse=True)
def prepare_database():
    Base.metadata.drop_all(
        bind=engine
    )
    Base.metadata.create_all(
        bind=engine
    )
    yield
def test_local_backend_is_default(
    monkeypatch,
):
    monkeypatch.setattr(
        settings,
        "file_storage_backend",
        "local",
    )
    assert (
        get_file_storage_backend()
        == "local"
    )
    assert (
        use_database_storage()
        is False
    )
def test_database_backend_is_supported(
    monkeypatch,
):
    monkeypatch.setattr(
        settings,
        "file_storage_backend",
        "database",
    )
    assert (
        use_database_storage()
        is True
    )
def test_invalid_backend_is_rejected(
    monkeypatch,
):
    monkeypatch.setattr(
        settings,
        "file_storage_backend",
        "invalid",
    )
    with pytest.raises(
        FileStorageConfigurationError
    ):
        get_file_storage_backend()
def test_storage_key_is_safe():
    assert (
        make_storage_key(
            "documents",
            "abc.pdf",
        )
        == "documents/abc.pdf"
    )
    with pytest.raises(ValueError):
        make_storage_key(
            "documents",
            "../abc.pdf",
        )
def test_blob_round_trip():
    with SessionLocal() as database:
        put_file_blob(
            database,
            storage_key=(
                "documents/test.pdf"
            ),
            content=b"%PDF-test",
            sha256="a" * 64,
            mime_type="application/pdf",
        )
        database.commit()
        blob = get_file_blob(
            database,
            "documents/test.pdf",
        )
        assert (
            blob.content
            == b"%PDF-test"
        )
        assert blob.size_bytes == 9
        assert blob.sha256 == "a" * 64
def test_blob_put_is_idempotent():
    with SessionLocal() as database:
        put_file_blob(
            database,
            storage_key=(
                "documents/test.pdf"
            ),
            content=b"one",
            sha256="a" * 64,
            mime_type="application/pdf",
        )
        database.commit()
        put_file_blob(
            database,
            storage_key=(
                "documents/test.pdf"
            ),
            content=b"two",
            sha256="b" * 64,
            mime_type="application/pdf",
        )
        database.commit()
        blob = get_file_blob(
            database,
            "documents/test.pdf",
        )
        assert blob.content == b"two"
        assert blob.sha256 == "b" * 64
def test_blob_delete():
    with SessionLocal() as database:
        put_file_blob(
            database,
            storage_key=(
                "candidates/test.pdf"
            ),
            content=b"%PDF-test",
            sha256="c" * 64,
            mime_type="application/pdf",
        )
        database.commit()
        deleted = delete_file_blob(
            database,
            "candidates/test.pdf",
        )
        database.commit()
        assert deleted is True
        with pytest.raises(
            DatabaseFileNotFoundError
        ):
            get_file_blob(
                database,
                "candidates/test.pdf",
            )
def test_database_backup_and_restore(
    tmp_path,
    monkeypatch,
):
    from backend.app.services.file_storage_service import (
        backup_local_file_to_database,
        restore_database_file,
    )
    monkeypatch.setattr(
        settings,
        "file_storage_backend",
        "database",
    )
    source = tmp_path / "source.pdf"
    source.write_bytes(
        b"%PDF-database-cache-test"
    )
    import hashlib
    digest = hashlib.sha256(
        source.read_bytes()
    ).hexdigest()
    with SessionLocal() as database:
        stored = backup_local_file_to_database(
            database,
            category="documents",
            stored_name="test.pdf",
            local_path=source,
            expected_sha256=digest,
            mime_type="application/pdf",
        )
        database.commit()
        assert stored is True
        source.unlink()
        restored = restore_database_file(
            database,
            category="documents",
            stored_name="test.pdf",
            local_path=source,
            expected_sha256=digest,
        )
        assert restored is True
        assert source.exists()
        assert (
            source.read_bytes()
            == b"%PDF-database-cache-test"
        )
def test_local_mode_does_not_use_database_cache(
    tmp_path,
    monkeypatch,
):
    from backend.app.services.file_storage_service import (
        backup_local_file_to_database,
    )
    monkeypatch.setattr(
        settings,
        "file_storage_backend",
        "local",
    )
    source = tmp_path / "local.pdf"
    source.write_bytes(
        b"%PDF-local-test"
    )
    import hashlib
    digest = hashlib.sha256(
        source.read_bytes()
    ).hexdigest()
    with SessionLocal() as database:
        stored = backup_local_file_to_database(
            database,
            category="documents",
            stored_name="local.pdf",
            local_path=source,
            expected_sha256=digest,
            mime_type="application/pdf",
        )
        assert stored is False
