"""Optional Postgres persistence for prototype project storage."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any
from uuid import uuid4


DATABASE_URL_ENV = "DATABASE_URL"
ARTIFACT_STORAGE_PATH_ENV = "ARTIFACT_STORAGE_PATH"
DEFAULT_ARTIFACT_STORAGE_PATH = "/data/artifacts"


class PersistenceUnavailable(RuntimeError):
    """Raised when persistence is requested without a configured database."""


def persistence_enabled() -> bool:
    return bool(os.getenv(DATABASE_URL_ENV))


def artifact_storage_path() -> Path:
    return Path(
        os.getenv(ARTIFACT_STORAGE_PATH_ENV, DEFAULT_ARTIFACT_STORAGE_PATH)
    )


def _connect():
    database_url = os.getenv(DATABASE_URL_ENV)
    if not database_url:
        raise PersistenceUnavailable("DATABASE_URL is not configured.")
    try:
        import psycopg
        from psycopg.rows import dict_row
    except ImportError as exc:
        raise PersistenceUnavailable("psycopg is not installed.") from exc
    return psycopg.connect(database_url, row_factory=dict_row)


def initialize_schema() -> None:
    if not persistence_enabled():
        return
    artifact_storage_path().mkdir(parents=True, exist_ok=True)
    with _connect() as conn:
        conn.execute(
            """
            create table if not exists projects (
                id text primary key,
                name text not null,
                description text not null default '',
                created_at timestamptz not null default now(),
                updated_at timestamptz not null default now(),
                deleted_at timestamptz
            )
            """
        )
        conn.execute(
            """
            create table if not exists project_state (
                project_id text primary key references projects(id),
                planning_state_json jsonb not null default '{}'::jsonb,
                target_region text not null default '',
                target_zone text not null default '',
                project_name text not null default '',
                updated_at timestamptz not null default now()
            )
            """
        )
        conn.execute(
            """
            create table if not exists project_artifacts (
                id text primary key,
                project_id text not null references projects(id),
                artifact_type text not null,
                original_filename text not null,
                stored_path text not null,
                content_type text not null default '',
                size_bytes bigint not null default 0,
                created_at timestamptz not null default now()
            )
            """
        )
        conn.execute(
            """
            create table if not exists project_events (
                id text primary key,
                project_id text not null references projects(id),
                event_type text not null,
                message text not null default '',
                created_at timestamptz not null default now()
            )
            """
        )


def create_project(name: str, description: str = "") -> dict[str, Any]:
    project_id = str(uuid4())
    with _connect() as conn:
        row = conn.execute(
            """
            insert into projects (id, name, description)
            values (%s, %s, %s)
            returning id, name, description, created_at, updated_at
            """,
            (project_id, name, description),
        ).fetchone()
        conn.execute(
            """
            insert into project_events (id, project_id, event_type, message)
            values (%s, %s, %s, %s)
            """,
            (str(uuid4()), project_id, "created", "Project created."),
        )
    return dict(row)


def list_projects() -> list[dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute(
            """
            select id, name, description, created_at, updated_at
            from projects
            where deleted_at is null
            order by updated_at desc, created_at desc
            """
        ).fetchall()
    return [dict(row) for row in rows]


def get_project(project_id: str) -> dict[str, Any] | None:
    with _connect() as conn:
        row = conn.execute(
            """
            select id, name, description, created_at, updated_at
            from projects
            where id = %s and deleted_at is null
            """,
            (project_id,),
        ).fetchone()
    return dict(row) if row else None


def update_project(
    project_id: str,
    name: str,
    description: str = "",
) -> dict[str, Any] | None:
    with _connect() as conn:
        row = conn.execute(
            """
            update projects
            set name = %s, description = %s, updated_at = now()
            where id = %s and deleted_at is null
            returning id, name, description, created_at, updated_at
            """,
            (name, description, project_id),
        ).fetchone()
        if row:
            conn.execute(
                """
                insert into project_events (id, project_id, event_type, message)
                values (%s, %s, %s, %s)
                """,
                (str(uuid4()), project_id, "updated", "Project updated."),
            )
    return dict(row) if row else None


def save_project_state(
    project_id: str,
    planning_state: dict[str, Any],
    target_region: str = "",
    target_zone: str = "",
    project_name: str = "",
) -> dict[str, Any]:
    try:
        from psycopg.types.json import Jsonb
    except ImportError as exc:
        raise PersistenceUnavailable("psycopg JSON support is unavailable.") from exc
    with _connect() as conn:
        row = conn.execute(
            """
            insert into project_state (
                project_id, planning_state_json, target_region,
                target_zone, project_name
            )
            values (%s, %s, %s, %s, %s)
            on conflict (project_id) do update set
                planning_state_json = excluded.planning_state_json,
                target_region = excluded.target_region,
                target_zone = excluded.target_zone,
                project_name = excluded.project_name,
                updated_at = now()
            returning project_id, planning_state_json, target_region,
                target_zone, project_name, updated_at
            """,
            (
                project_id,
                Jsonb(planning_state),
                target_region,
                target_zone,
                project_name,
            ),
        ).fetchone()
        conn.execute(
            "update projects set updated_at = now() where id = %s",
            (project_id,),
        )
    return dict(row)


def get_project_state(project_id: str) -> dict[str, Any] | None:
    with _connect() as conn:
        row = conn.execute(
            """
            select project_id, planning_state_json, target_region,
                target_zone, project_name, updated_at
            from project_state
            where project_id = %s
            """,
            (project_id,),
        ).fetchone()
    return dict(row) if row else None


def save_artifact(
    project_id: str,
    artifact_type: str,
    original_filename: str,
    content_type: str,
    source_file,
) -> dict[str, Any]:
    artifact_id = str(uuid4())
    project_dir = artifact_storage_path() / project_id
    project_dir.mkdir(parents=True, exist_ok=True)
    safe_name = Path(original_filename or artifact_type).name
    stored_path = project_dir / f"{artifact_id}-{safe_name}"
    source_file.seek(0)
    with stored_path.open("wb") as output:
        shutil.copyfileobj(source_file, output)
    size_bytes = stored_path.stat().st_size
    with _connect() as conn:
        row = conn.execute(
            """
            insert into project_artifacts (
                id, project_id, artifact_type, original_filename,
                stored_path, content_type, size_bytes
            )
            values (%s, %s, %s, %s, %s, %s, %s)
            returning id, project_id, artifact_type, original_filename,
                stored_path, content_type, size_bytes, created_at
            """,
            (
                artifact_id,
                project_id,
                artifact_type,
                safe_name,
                str(stored_path),
                content_type or "",
                size_bytes,
            ),
        ).fetchone()
        conn.execute(
            "update projects set updated_at = now() where id = %s",
            (project_id,),
        )
    return dict(row)


def list_artifacts(project_id: str) -> list[dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute(
            """
            select id, project_id, artifact_type, original_filename,
                stored_path, content_type, size_bytes, created_at
            from project_artifacts
            where project_id = %s
            order by created_at desc
            """,
            (project_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def delete_project(project_id: str) -> None:
    with _connect() as conn:
        conn.execute(
            "update projects set deleted_at = now() where id = %s",
            (project_id,),
        )
    project_dir = artifact_storage_path() / project_id
    if project_dir.exists() and project_dir.is_dir():
        shutil.rmtree(project_dir)
