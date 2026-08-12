from hashlib import sha256
from pathlib import Path
from uuid import uuid4
from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.models.file_blob import FileBlob
VALID_FILE_STORAGE_BACKENDS = {
    "local",
    "database",
}
class FileStorageConfigurationError(
    ValueError
):
    pass
class DatabaseFileNotFoundError(
    FileNotFoundError
):
    pass
class DatabaseFileIntegrityError(
    ValueError
):
    pass
def get_file_storage_backend() -> str:
    backend = (
        settings.file_storage_backend
        .strip()
        .lower()
    )
    if backend not in VALID_FILE_STORAGE_BACKENDS:
        raise FileStorageConfigurationError(
            "FILE_STORAGE_BACKEND must be "
            "'local' or 'database'."
        )
    return backend
def use_database_storage() -> bool:
    return (
        get_file_storage_backend()
        == "database"
    )
def make_storage_key(
    category: str,
    stored_name: str,
) -> str:
    clean_category = (
        category.strip().strip("/")
    )
    clean_name = (
        stored_name.strip().replace("\\", "/")
    )
    if (
        not clean_category
        or not clean_name
        or "/" in clean_name
        or clean_name in {".", ".."}
    ):
        raise ValueError(
            "Invalid storage key."
        )
    return (
        f"{clean_category}/"
        f"{clean_name}"
    )
def put_file_blob(
    database: Session,
    *,
    storage_key: str,
    content: bytes,
    sha256: str,
    mime_type: str,
) -> FileBlob:
    existing = database.scalar(
        select(FileBlob).where(
            FileBlob.storage_key
            == storage_key
        )
    )
    if existing is None:
        blob = FileBlob(
            storage_key=storage_key,
            content=content,
            size_bytes=len(content),
            sha256=sha256,
            mime_type=mime_type,
        )
        database.add(blob)
        database.flush()
        return blob
    existing.content = content
    existing.size_bytes = len(content)
    existing.sha256 = sha256
    existing.mime_type = mime_type
    database.flush()
    return existing
def get_file_blob(
    database: Session,
    storage_key: str,
) -> FileBlob:
    blob = database.scalar(
        select(FileBlob).where(
            FileBlob.storage_key
            == storage_key
        )
    )
    if blob is None:
        raise DatabaseFileNotFoundError(
            "The stored database file "
            "could not be found."
        )
    return blob
def delete_file_blob(
    database: Session,
    storage_key: str,
) -> bool:
    result = database.execute(
        delete(FileBlob).where(
            FileBlob.storage_key
            == storage_key
        )
    )
    return bool(
        result.rowcount
        and result.rowcount > 0
    )

def backup_local_file_to_database(
    database: Session,
    *,
    category: str,
    stored_name: str,
    local_path: Path,
    expected_sha256: str,
    mime_type: str,
) -> bool:
    if not use_database_storage():
        return False
    if (
        not local_path.exists()
        or not local_path.is_file()
    ):
        raise DatabaseFileNotFoundError(
            "The local file could not be found "
            "for database storage."
        )
    content = local_path.read_bytes()
    actual_sha256 = sha256(
        content
    ).hexdigest()
    if actual_sha256 != expected_sha256:
        raise DatabaseFileIntegrityError(
            "The file checksum does not match "
            "the expected SHA-256 value."
        )
    storage_key = make_storage_key(
        category,
        stored_name,
    )
    put_file_blob(
        database,
        storage_key=storage_key,
        content=content,
        sha256=actual_sha256,
        mime_type=mime_type,
    )
    return True
def restore_database_file(
    database: Session,
    *,
    category: str,
    stored_name: str,
    local_path: Path,
    expected_sha256: str,
) -> bool:
    if (
        local_path.exists()
        and local_path.is_file()
    ):
        return True
    if not use_database_storage():
        return False
    storage_key = make_storage_key(
        category,
        stored_name,
    )
    blob = get_file_blob(
        database,
        storage_key,
    )
    actual_sha256 = sha256(
        blob.content
    ).hexdigest()
    if (
        blob.sha256 != expected_sha256
        or actual_sha256 != expected_sha256
    ):
        raise DatabaseFileIntegrityError(
            "The stored database file failed "
            "its integrity check."
        )
    local_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    temporary_path = local_path.with_name(
        f".{local_path.name}."
        f"{uuid4().hex}.restore"
    )
    try:
        temporary_path.write_bytes(
            blob.content
        )
        temporary_path.replace(
            local_path
        )
    finally:
        if temporary_path.exists():
            temporary_path.unlink()
    return True
def delete_database_file(
    database: Session,
    *,
    category: str,
    stored_name: str,
) -> bool:
    if not use_database_storage():
        return False
    storage_key = make_storage_key(
        category,
        stored_name,
    )
    return delete_file_blob(
        database,
        storage_key,
    )
