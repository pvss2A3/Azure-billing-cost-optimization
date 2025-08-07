import hashlib
import json
import pytest

def test_checksum_generation():
    data = {"id": "123", "amount": 100, "created_at": "2025-01-01T00:00:00Z"}
    data_json = json.dumps(data, sort_keys=True)
    checksum = hashlib.sha256(data_json.encode()).hexdigest()
    assert len(checksum) == 64  # SHA256 produces a 64-character hex string
    assert checksum == hashlib.sha256(data_json.encode()).hexdigest()  # Ensure consistency

def test_checksum_mismatch():
    data = {"id": "123", "amount": 100}
    modified_data = {"id": "123", "amount": 200}
    data_json = json.dumps(data, sort_keys=True)
    modified_json = json.dumps(modified_data, sort_keys=True)
    checksum = hashlib.sha256(data_json.encode()).hexdigest()
    modified_checksum = hashlib.sha256(modified_json.encode()).hexdigest()
    assert checksum != modified_checksum  # Different data produces different checksum
