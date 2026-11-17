import pytest


class FakeBlob:
    """Blob en memoria con la misma interfaz mínima que google.cloud.storage.Blob."""

    def __init__(self, bucket: "FakeBucket", name: str):
        self._bucket = bucket
        self.name = name

    def download_as_bytes(self) -> bytes:
        return self._bucket.objects[self.name]

    def upload_from_string(self, body: bytes, content_type: str | None = None) -> None:
        self._bucket.objects[self.name] = body


class FakeBucket:
    """Bucket en memoria: `objects` mapea nombre de objeto -> bytes."""

    def __init__(self):
        self.objects: dict[str, bytes] = {}

    def blob(self, name: str) -> FakeBlob:
        return FakeBlob(self, name)

    def list_blobs(self, prefix: str = "") -> list[FakeBlob]:
        return [
            FakeBlob(self, name)
            for name in sorted(self.objects)
            if name.startswith(prefix)
        ]


@pytest.fixture
def fake_bucket() -> FakeBucket:
    return FakeBucket()
