"""
Embedding pipeline - sync xe tu SQL Server sang Qdrant.
"""

import hashlib
import logging
from datetime import datetime, timezone

from qdrant_client.models import PointStruct

from app.config import get_settings
from app.db import sqlserver
from app.db.qdrant import get_qdrant_client
from app.services.embedding import embed_batch

logger = logging.getLogger(__name__)


VEHICLE_QUERY = """
SELECT
    v.id,
    v.title,
    v.price,
    v.year,
    v.mileage,
    v.fuel,
    v.transmission,
    v.body_style,
    v.origin,
    v.description,
    v.status,
    v.updated_at,
    c.name AS loai_xe,
    sc.name AS dong_xe,
    b.name AS chi_nhanh,
    b.address AS dia_chi
FROM Vehicles v
JOIN Categories c ON v.category_id = c.id
JOIN Subcategories sc ON v.subcategory_id = sc.id
LEFT JOIN Branches b ON v.branch_id = b.id
WHERE v.status = 'Available'
  AND v.is_deleted = 0
"""


def serialize_car_to_text(row: dict) -> str:
    """Chuyen 1 row xe thanh van ban co cau truc de embed."""
    parts = [
        f"Xe: {row['title']}",
        f"Loai: {row['loai_xe']} - {row['dong_xe']}",
        f"Nam san xuat: {row['year']}",
        f"Gia ban: {int(row['price']):,} VND" if row.get("price") else None,
        f"So km: {row['mileage']:,} km" if row.get("mileage") else None,
        f"Nhien lieu: {row['fuel']}" if row.get("fuel") else None,
        f"Hop so: {row['transmission']}" if row.get("transmission") else None,
        f"Kieu dang: {row['body_style']}" if row.get("body_style") else None,
        f"Xuat xu: {row['origin']}" if row.get("origin") else None,
        f"Chi nhanh: {row['chi_nhanh']}" if row.get("chi_nhanh") else None,
        f"Mo ta: {row['description']}" if row.get("description") else None,
    ]
    return "\n".join(part for part in parts if part)


def _normalize_updated_at(value) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        else:
            value = value.astimezone(timezone.utc)
        return value.isoformat(timespec="seconds")
    return str(value)


def _build_content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _build_vehicle_payload(row: dict, text: str) -> dict:
    return {
        "vehicle_id": int(row["id"]),
        "title": row["title"],
        "loai_xe": row.get("loai_xe"),
        "dong_xe": row.get("dong_xe"),
        "gia": float(row["price"]) if row.get("price") else 0,
        "chi_nhanh": row.get("chi_nhanh"),
        "status": row["status"],
        "fuel": row.get("fuel"),
        "transmission": row.get("transmission"),
        "body_style": row.get("body_style"),
        "year": row.get("year"),
        "origin": row.get("origin"),
        "updated_at": _normalize_updated_at(row.get("updated_at")),
        "content_hash": _build_content_hash(text),
        "text": text,
    }


def _scroll_existing_points(collection: str, client) -> dict[int, dict]:
    existing: dict[int, dict] = {}
    offset = None

    while True:
        points, next_offset = client.scroll(
            collection_name=collection,
            limit=1000,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )
        for point in points:
            existing[int(point.id)] = point.payload or {}
        if next_offset is None:
            break
        offset = next_offset

    return existing


def _upsert_rows(rows: list[dict], collection: str, client) -> int:
    if not rows:
        return 0

    settings = get_settings()
    texts = [serialize_car_to_text(row) for row in rows]
    batch_size = max(1, settings.EMBEDDING_BATCH_SIZE)
    vectors = []

    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i : i + batch_size]
        vectors.extend(embed_batch(batch_texts, batch_size=batch_size))
        logger.info(
            "Embedded batch %d/%d",
            i // batch_size + 1,
            (len(texts) - 1) // batch_size + 1,
        )

    upsert_batch = 100
    for i in range(0, len(rows), upsert_batch):
        batch_rows = rows[i : i + upsert_batch]
        batch_texts = texts[i : i + upsert_batch]
        batch_vectors = vectors[i : i + upsert_batch]
        points = []

        for row, text, vec in zip(batch_rows, batch_texts, batch_vectors):
            points.append(
                PointStruct(
                    id=int(row["id"]),
                    vector=vec,
                    payload=_build_vehicle_payload(row, text),
                )
            )

        client.upsert(collection_name=collection, points=points)

    return len(rows)


def sync_vehicles_if_changed() -> int:
    """
    So sanh SQL voi Qdrant.
    Chi embed/upsert xe moi hoac thay doi, va xoa xe stale.
    """
    settings = get_settings()
    client = get_qdrant_client()
    collection = settings.QDRANT_COLLECTION

    logger.info("Checking vehicle delta between SQL Server and Qdrant...")
    rows = sqlserver.query(VEHICLE_QUERY, timeout=30)
    logger.info("Fetched %d available vehicles from SQL Server", len(rows))

    existing_points = _scroll_existing_points(collection, client)
    current_ids = {int(row["id"]) for row in rows}
    stale_ids = sorted(set(existing_points) - current_ids)

    changed_rows = []
    for row in rows:
        vehicle_id = int(row["id"])
        text = serialize_car_to_text(row)
        content_hash = _build_content_hash(text)
        updated_at = _normalize_updated_at(row.get("updated_at"))
        existing_payload = existing_points.get(vehicle_id)

        if not existing_payload:
            changed_rows.append(row)
            continue

        if (
            existing_payload.get("content_hash") != content_hash
            or existing_payload.get("updated_at") != updated_at
        ):
            changed_rows.append(row)

    if stale_ids:
        client.delete(collection_name=collection, points_selector=stale_ids)
        logger.info("Removed %d stale vehicles from Qdrant", len(stale_ids))

    if not changed_rows:
        logger.info("No new or changed vehicles detected; skip embedding")
        return 0

    logger.info("Detected %d new/changed vehicles; embedding delta only", len(changed_rows))
    synced = _upsert_rows(changed_rows, collection, client)
    logger.info("Delta sync complete: %d vehicles upserted", synced)
    return synced


def sync_all_vehicles() -> int:
    """
    Dong bo toan bo xe Available tu SQL Server sang Qdrant.
    Ham nay giu lai cho admin full sync.
    """
    settings = get_settings()
    client = get_qdrant_client()
    collection = settings.QDRANT_COLLECTION

    logger.info("Starting full vehicle sync pipeline...")
    rows = sqlserver.query(VEHICLE_QUERY, timeout=30)
    logger.info("Fetched %d available vehicles from SQL Server", len(rows))

    if not rows:
        logger.warning("No available vehicles found")
        return 0

    synced = _upsert_rows(rows, collection, client)
    logger.info("Full sync complete: %d vehicles upserted to Qdrant", synced)
    _remove_stale_vehicles(rows, collection, client)
    return synced


def sync_changed_vehicles() -> int:
    """
    Incremental sync theo diff SQL vs Qdrant.
    Khong full sync lai khi app restart.
    """
    return sync_vehicles_if_changed()


def _remove_stale_vehicles(current_rows: list[dict], collection: str, client):
    """Xoa cac point trong Qdrant ma xe da khong con Available."""
    current_ids = {int(row["id"]) for row in current_rows}

    try:
        existing_points = _scroll_existing_points(collection, client)
        stale_ids = sorted(set(existing_points) - current_ids)

        if stale_ids:
            client.delete(collection_name=collection, points_selector=stale_ids)
            logger.info("Removed %d stale vehicles from Qdrant", len(stale_ids))
        else:
            logger.info("No stale vehicles to remove")
    except Exception:
        logger.exception("Error removing stale vehicles")


def remove_vehicle_by_id(vehicle_id: int):
    """Xoa 1 xe khoi Qdrant ngay lap tuc."""
    settings = get_settings()
    client = get_qdrant_client()
    try:
        client.delete(
            collection_name=settings.QDRANT_COLLECTION,
            points_selector=[vehicle_id],
        )
        logger.info("Removed vehicle %d from Qdrant", vehicle_id)
    except Exception:
        logger.exception("Error removing vehicle %d from Qdrant", vehicle_id)
