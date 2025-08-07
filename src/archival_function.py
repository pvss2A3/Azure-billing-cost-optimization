import azure.functions as func
import azure.cosmos.cosmos_client as cosmos_client
from azure.storage.blob import BlobServiceClient
import hashlib
import json
import os
from datetime import datetime, timedelta

COSMOS_ENDPOINT = os.environ["COSMOS_ENDPOINT"]
COSMOS_KEY = os.environ["COSMOS_KEY"]
BLOB_CONNECTION_STRING = os.environ["BLOB_CONNECTION_STRING"]
COSMOS_DB_NAME = "BillingDB"
COSMOS_CONTAINER_NAME = "BillingRecords"
BLOB_CONTAINER_NAME = "billing-archives"

def main(documents: func.DocumentList) -> None:
    cosmos_client_instance = cosmos_client.CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
    database = cosmos_client_instance.get_database_client(COSMOS_DB_NAME)
    container = database.get_container_client(COSMOS_CONTAINER_NAME)
    blob_service_client = BlobServiceClient.from_connection_string(BLOB_CONNECTION_STRING)
    blob_container_client = blob_service_client.get_container_client(BLOB_CONTAINER_NAME)

    for doc in documents:
        record = dict(doc)
        created_at = datetime.fromisoformat(record["created_at"])
        if datetime.utcnow() - created_at > timedelta(days=90):  # Older than 3 months
            # Calculate checksum
            record_json = json.dumps(record, sort_keys=True)
            checksum = hashlib.sha256(record_json.encode()).hexdigest()

            # Upload to Blob Storage
            blob_name = f"billing/{record['id']}.json"
            blob_client = blob_container_client.get_blob_client(blob_name)
            blob_client.upload_blob(record_json, overwrite=True)

            # Create metadata document
            metadata = {
                "id": f"meta_{record['id']}",
                "record_id": record["id"],
                "blob_uri": blob_client.url,
                "checksum": checksum,
                "created_at": record["created_at"],
                "customer_id": record["customer_id"],
                "_type": "metadata"
            }
            container.upsert_item(metadata)

            # Delete original record
            container.delete_item(doc["id"], partition_key=doc["customer_id"])
