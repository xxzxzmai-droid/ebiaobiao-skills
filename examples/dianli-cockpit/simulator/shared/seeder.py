"""Idempotent batch seeding.

Strategy: pull existing records (key fields only), build a set of composite
keys, filter input records to those not already present, then write in
batches of 10 (vika REST limit) — handled by VikaClient.
"""
import logging
from typing import List, Sequence

logger = logging.getLogger(__name__)


def seed_table(client, dst_id: str, records: List[dict],
               key_fields: Sequence[str], *, dry_run: bool = False) -> int:
    """Seed `records` into `dst_id`, skipping any whose composite key already
    exists. Returns count of records actually inserted (or that would be on
    a real run, when dry_run=True)."""
    existing_keys = set()
    try:
        existing = client.list_all_records(dst_id, fields=list(key_fields))
        for r in existing:
            f = r.get("fields") or {}
            key = tuple(f.get(k) for k in key_fields)
            existing_keys.add(key)
    except Exception as e:  # noqa: BLE001
        logger.warning("could not list existing records for %s: %s; treating as empty",
                       dst_id, e)

    to_insert = []
    for rec in records:
        key = tuple(rec.get(k) for k in key_fields)
        if key in existing_keys:
            continue
        to_insert.append(rec)

    logger.info("table %s: %d new / %d total / %d existing",
                dst_id, len(to_insert), len(records), len(existing_keys))

    if dry_run:
        return len(to_insert)

    if to_insert:
        client.create_records(dst_id, to_insert)
    return len(to_insert)
