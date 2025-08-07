# Tests

This directory contains unit tests for the Azure billing records cost optimization solution.

- `test_checksum.py`: Validates SHA256 checksum generation and mismatch detection for data integrity.

To run tests:
    ```bash
    pip install pytest
    pytest tests/

Add more tests for:
    - Mocked Cosmos DB queries and Blob Storage retrievals.
    - API handler edge cases (e.g., missing metadata, corrupted data).
