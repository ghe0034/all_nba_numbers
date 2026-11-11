from nba_ingest.gcs_uploader import upload_bytes


class FakeBlob:
    def __init__(self, name):
        self.name = name
        self.uploads = []

    def upload_from_string(self, data, content_type=None):
        self.uploads.append({"data": data, "content_type": content_type})


class FakeBucket:
    def __init__(self):
        self.blobs = {}

    def blob(self, name):
        self.blobs[name] = FakeBlob(name)
        return self.blobs[name]


def test_upload_writes_bytes_unchanged_as_json_to_object_path():
    bucket = FakeBucket()
    body = b'{ "resultSets" : [] }\n'

    upload_bytes(bucket, "bronze/demo/season=2025-26/download_date=2026-11-11/demo.json", body)

    blob = bucket.blobs["bronze/demo/season=2025-26/download_date=2026-11-11/demo.json"]
    assert blob.uploads == [{"data": body, "content_type": "application/json"}]
