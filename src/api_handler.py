import azure.functions as func
import azure.cosmos.cosmos_client as cosmos_client
from azure.storage.blob import BlobServiceClient
import json
import os
import hashlib

COSMOS_ENDPOINT = os.environ["COSMOS_ENDPOINT"]
COSMOS_KEY = os.environ["COSMOS_KEY"]
BLOB_CONNECTION_STRING = os.environ["BLOB_CONNECTION_STRING"]
COSMOS_DB_NAME = "BillingDB"
COSMOS_CONTAINER_NAME = "BillingRecords"
BLOB_CONTAINER_NAME = "billing-archives"

def main(req: func.HttpRequest) -> func.HttpResponse:
    record_id = req.route_params.get("id")
    cosmos_client_instance = cosmos_client.CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
    database = cosmos_client_instance.get_database_client(COSMOS_DB_NAME)
    container = database.get_container_client(COSMOS_CONTAINER_NAME)

    try:
        # Try fetching from Cosmos DB
        record = container.read_item(item=record_id, partition_key=record_id)
        return func.HttpResponse(json.dumps(record), status_code=200, mimetype="application/json")
    except:
        # Check metadata for archived record
        query = f"SELECT * FROM c WHERE c._type = 'metadata' AND c.record_id = '{record_id}'"
        metadata_items = list(container.query_items(query, enable_cross_partition_query=True))
        if not metadata_items:
            return func.HttpResponse("Record not found", status_code=404)

        metadata = metadata_items[0]
        blob_service_client = BlobServiceClient.from_connection_string(BLOB_CONNECTION_STRING)
        blob_container_client = blob_service_client.get_container_client(BLOB_CONTAINER_NAME)
        blob_client = blob_container_client.get_blob_client(f"billing/{record_id}.json")

        # Fetch from Blob Storage
        blob_data = blob_client.download_blob().readall().decode()
        record = json.loads(blob_data)

        # Verify checksum
        calculated_checksum = hashlib.sha256(blob_data.encode()).hexdigest()
        if calculated_checksum != metadata["checksum"]:
            return func.HttpResponse("Data corruption detected", status_code=500)

        return func.HttpResponse(blob_data, status_code=200, mimetype="application/json")
