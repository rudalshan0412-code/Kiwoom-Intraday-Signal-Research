from __future__ import annotations

import gzip
import hashlib
import json
import shutil
import sqlite3

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable
from zoneinfo import ZoneInfo


KST = ZoneInfo("Asia/Seoul")


DEFAULT_TABLES = (
    "ticks",
    "orderbooks",
    "signals",
    "future_outcomes",
    "engine_events",
    "universe_events",
    "order_events",
    "fills",
    "trades",
)


@dataclass(frozen=True)
class WeeklyPaths:
    week_id: str

    live_db: Path
    archive_dir: Path

    snapshot_db: Path
    compressed_db: Path
    sha256_file: Path
    manifest_file: Path


def get_week_id(
    when: datetime | None = None,
) -> str:

    if when is None:
        when = datetime.now(KST)

    if when.tzinfo is None:
        when = when.replace(
            tzinfo=KST
        )

    local = when.astimezone(
        KST
    )

    iso = local.isocalendar()

    return (
        f"{iso.year}-W"
        f"{iso.week:02d}"
    )


def get_weekly_paths(
    project_root: str | Path,
    *,
    when: datetime | None = None,
) -> WeeklyPaths:

    root = Path(
        project_root
    ).resolve()

    week_id = get_week_id(
        when
    )

    live_dir = (
        root
        / "data"
        / "weekly"
        / "live"
    )

    archive_dir = (
        root
        / "data"
        / "weekly"
        / "archive"
        / week_id
    )

    live_db = (
        live_dir
        / f"scalping_{week_id}.db"
    )

    snapshot_db = (
        archive_dir
        / f"scalping_{week_id}.db"
    )

    compressed_db = (
        archive_dir
        / f"scalping_{week_id}.db.gz"
    )

    sha256_file = (
        archive_dir
        / f"scalping_{week_id}.db.gz.sha256"
    )

    manifest_file = (
        archive_dir
        / f"manifest_{week_id}.json"
    )

    return WeeklyPaths(
        week_id=week_id,
        live_db=live_db,
        archive_dir=archive_dir,
        snapshot_db=snapshot_db,
        compressed_db=compressed_db,
        sha256_file=sha256_file,
        manifest_file=manifest_file,
    )


def copy_schema_only(
    source_db: str | Path,
    target_db: str | Path,
) -> None:

    source_path = Path(
        source_db
    )

    target_path = Path(
        target_db
    )

    if not source_path.exists():

        raise FileNotFoundError(
            f"Schema source DB 없음: {source_path}"
        )

    target_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if target_path.exists():
        return

    source = sqlite3.connect(
        source_path
    )

    target = sqlite3.connect(
        target_path
    )

    try:

        rows = source.execute(
            """
            SELECT
                type,
                name,
                sql
            FROM sqlite_master
            WHERE
                type IN (
                    'table',
                    'index',
                    'trigger',
                    'view'
                )
                AND sql IS NOT NULL
                AND name NOT LIKE 'sqlite_%'
            ORDER BY
                CASE type
                    WHEN 'table' THEN 0
                    WHEN 'index' THEN 1
                    WHEN 'trigger' THEN 2
                    ELSE 3
                END,
                name
            """
        ).fetchall()

        for (
            object_type,
            name,
            sql,
        ) in rows:

            try:

                target.execute(
                    sql
                )

            except sqlite3.OperationalError as exc:

                raise RuntimeError(
                    "Schema 복사 실패: "
                    f"type={object_type}, "
                    f"name={name}, "
                    f"error={exc}"
                ) from exc

        target.commit()

    finally:

        source.close()
        target.close()


def ensure_weekly_database(
    project_root: str | Path,
    *,
    schema_source_db: str | Path,
    when: datetime | None = None,
) -> WeeklyPaths:

    paths = get_weekly_paths(
        project_root,
        when=when,
    )

    paths.live_db.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    paths.archive_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    if not paths.live_db.exists():

        copy_schema_only(
            schema_source_db,
            paths.live_db,
        )

    quick_check_database(
        paths.live_db
    )

    return paths


def quick_check_database(
    db_path: str | Path,
) -> str:

    path = Path(
        db_path
    )

    if not path.exists():

        raise FileNotFoundError(
            path
        )

    conn = sqlite3.connect(
        path,
        timeout=30.0,
    )

    try:

        result = conn.execute(
            "PRAGMA quick_check"
        ).fetchone()[0]

    finally:

        conn.close()

    if str(result).lower() != "ok":

        raise RuntimeError(
            f"SQLite quick_check 실패: "
            f"{path}: {result}"
        )

    return str(
        result
    )


def table_counts(
    db_path: str | Path,
    tables: Iterable[str] = DEFAULT_TABLES,
) -> dict[str, int]:

    path = Path(
        db_path
    )

    conn = sqlite3.connect(
        path,
        timeout=30.0,
    )

    result: dict[
        str,
        int,
    ] = {}

    try:

        existing_tables = {
            row[0]
            for row in conn.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type='table'
                """
            ).fetchall()
        }

        for table in tables:

            if table not in existing_tables:

                result[
                    table
                ] = 0

                continue

            count = conn.execute(
                f'SELECT COUNT(*) FROM "{table}"'
            ).fetchone()[0]

            result[
                table
            ] = int(
                count
            )

    finally:

        conn.close()

    return result


def snapshot_database(
    source_db: str | Path,
    destination_db: str | Path,
) -> None:

    source_path = Path(
        source_db
    )

    destination_path = Path(
        destination_db
    )

    if not source_path.exists():

        raise FileNotFoundError(
            source_path
        )

    destination_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temp_path = (
        destination_path.with_suffix(
            destination_path.suffix
            + ".tmp"
        )
    )

    if temp_path.exists():
        temp_path.unlink()

    source = sqlite3.connect(
        source_path,
        timeout=30.0,
    )

    destination = sqlite3.connect(
        temp_path,
        timeout=30.0,
    )

    try:

        source.backup(
            destination
        )

        destination.commit()

    finally:

        destination.close()
        source.close()

    quick_check_database(
        temp_path
    )

    temp_path.replace(
        destination_path
    )


def gzip_file(
    source: str | Path,
    destination: str | Path,
) -> None:

    source_path = Path(
        source
    )

    destination_path = Path(
        destination
    )

    temp_path = (
        destination_path.with_suffix(
            destination_path.suffix
            + ".tmp"
        )
    )

    if temp_path.exists():
        temp_path.unlink()

    with source_path.open(
        "rb"
    ) as src:

        with gzip.open(
            temp_path,
            "wb",
            compresslevel=6,
        ) as dst:

            shutil.copyfileobj(
                src,
                dst,
                length=1024 * 1024,
            )

    temp_path.replace(
        destination_path
    )


def sha256_file(
    path: str | Path,
) -> str:

    file_path = Path(
        path
    )

    digest = hashlib.sha256()

    with file_path.open(
        "rb"
    ) as handle:

        while True:

            chunk = handle.read(
                1024 * 1024
            )

            if not chunk:
                break

            digest.update(
                chunk
            )

    return digest.hexdigest()


def archive_week(
    paths: WeeklyPaths,
    *,
    runtime_path: str | Path | None = None,
    ml_config_path: str | Path | None = None,
) -> dict:

    paths.archive_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ========================================================
    # 1. Source integrity
    # ========================================================

    source_quick_check = (
        quick_check_database(
            paths.live_db
        )
    )

    source_counts = (
        table_counts(
            paths.live_db
        )
    )

    # ========================================================
    # 2. SQLite safe snapshot
    # ========================================================

    snapshot_database(
        paths.live_db,
        paths.snapshot_db,
    )

    snapshot_quick_check = (
        quick_check_database(
            paths.snapshot_db
        )
    )

    snapshot_counts = (
        table_counts(
            paths.snapshot_db
        )
    )

    if (
        source_counts
        != snapshot_counts
    ):

        raise RuntimeError(
            "Snapshot row count 불일치: "
            f"source={source_counts}, "
            f"snapshot={snapshot_counts}"
        )

    # ========================================================
    # 3. Compress
    # ========================================================

    gzip_file(
        paths.snapshot_db,
        paths.compressed_db,
    )

    compressed_hash = (
        sha256_file(
            paths.compressed_db
        )
    )

    paths.sha256_file.write_text(
        (
            compressed_hash
            + "  "
            + paths.compressed_db.name
            + "\n"
        ),
        encoding="utf-8",
    )

    # ========================================================
    # 4. Runtime/config hashes
    # ========================================================

    runtime_hash = None
    ml_config_hash = None

    if runtime_path is not None:

        runtime = Path(
            runtime_path
        )

        if runtime.exists():

            runtime_hash = (
                sha256_file(
                    runtime
                )
            )

    if ml_config_path is not None:

        ml_config = Path(
            ml_config_path
        )

        if ml_config.exists():

            ml_config_hash = (
                sha256_file(
                    ml_config
                )
            )

    # ========================================================
    # 5. Manifest
    # ========================================================

    manifest = {
        "week_id":
            paths.week_id,

        "created_at":
            datetime.now(
                KST
            ).isoformat(
                timespec="seconds"
            ),

        "source_database":
            str(
                paths.live_db
            ),

        "snapshot_database":
            str(
                paths.snapshot_db
            ),

        "compressed_database":
            str(
                paths.compressed_db
            ),

        "source_quick_check":
            source_quick_check,

        "snapshot_quick_check":
            snapshot_quick_check,

        "row_counts":
            snapshot_counts,

        "compressed_sha256":
            compressed_hash,

        "runtime_sha256":
            runtime_hash,

        "ml_config_sha256":
            ml_config_hash,

        "compressed_size_bytes":
            paths.compressed_db.stat().st_size,

        "snapshot_size_bytes":
            paths.snapshot_db.stat().st_size,
    }

    paths.manifest_file.write_text(
        json.dumps(
            manifest,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    return manifest
