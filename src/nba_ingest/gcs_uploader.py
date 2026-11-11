"""Subida de bytes crudos a Google Cloud Storage."""

from typing import Any

from google.cloud import storage

JSON_CONTENT_TYPE = "application/json"


def make_bucket(project: str | None, bucket_name: str) -> Any:
    """Crea el cliente de GCS y devuelve el bucket de destino."""
    return storage.Client(project=project).bucket(bucket_name)


def upload_bytes(bucket: Any, object_name: str, body: bytes) -> None:
    """Sube `body` tal cual como objeto JSON en `object_name`."""
    blob = bucket.blob(object_name)
    blob.upload_from_string(body, content_type=JSON_CONTENT_TYPE)
