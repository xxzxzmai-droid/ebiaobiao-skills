"""Create or reuse datasheets and ensure all schema fields exist."""
from typing import Iterable, Dict
import logging

logger = logging.getLogger(__name__)


def bootstrap_schemas(client, schemas: Iterable[dict]) -> Dict[str, str]:
    """For each schema, create the datasheet if missing and add any missing fields.

    Returns: {table_name: datasheet_id}
    """
    result: Dict[str, str] = {}

    for s in schemas:
        name = s["name"]
        existing = client.search_nodes(query=name, type="Datasheet")
        existing_match = [n for n in existing if n.get("name") == name]
        if existing_match:
            dst_id = existing_match[0]["id"]
            logger.info("reuse datasheet: %s -> %s", name, dst_id)
        else:
            created = client.create_datasheet(name)
            dst_id = created["id"]
            logger.info("created datasheet: %s -> %s", name, dst_id)

        result[name] = dst_id

        existing_field_names = {f["name"] for f in client.list_fields(dst_id)}
        for field in s["fields"]:
            if field["name"] in existing_field_names:
                continue
            client.create_field(
                dst_id,
                name=field["name"],
                type=field["type"],
                property=field.get("property"),
            )
            logger.info("  + field: %s (%s)", field["name"], field["type"])

    return result
