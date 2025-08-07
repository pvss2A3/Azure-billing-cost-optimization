#!/bin/bash

# Variables
RESOURCE_GROUP="billing-optimization-rg"
LOCATION="eastus"
COSMOS_DB_ACCOUNT="billing-cosmos-db"
COSMOS_DB_NAME="BillingDB"
COSMOS_CONTAINER_NAME="BillingRecords"
STORAGE_ACCOUNT="billingarchives"
BLOB_CONTAINER="billing-archives"
FUNCTION_APP="billing-functions"

# Create resource group
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create Cosmos DB account
az cosmosdb create --name $COSMOS_DB_ACCOUNT --resource-group $RESOURCE_GROUP --locations regionName=$LOCATION

# Create Cosmos DB database and container
az cosmosdb sql database create --account-name $COSMOS_DB_ACCOUNT --resource-group $RESOURCE_GROUP --name $COSMOS_DB_NAME
az cosmosdb sql container create --account-name $COSMOS_DB_ACCOUNT --resource-group $RESOURCE_GROUP --database-name $COSMOS_DB_NAME --name $COSMOS_CONTAINER_NAME --partition-key-path "/customer_id"

# Create Storage Account and Blob Container
az storage account create --name $STORAGE_ACCOUNT --resource-group $RESOURCE_GROUP --location $LOCATION --sku Standard_LRS
az storage container create --name $BLOB_CONTAINER --account-name $STORAGE_ACCOUNT

# Create Function App
az functionapp create --name $FUNCTION_APP --resource-group $RESOURCE_GROUP --consumption-plan-location $LOCATION --runtime python --runtime-version 3.9 --functions-version 4

# Configure Function App environment variables
az functionapp config appsettings set --name $FUNCTION_APP --resource-group $RESOURCE_GROUP --settings "COSMOS_ENDPOINT=https://$COSMOS_DB_ACCOUNT.documents.azure.com:443/" "COSMOS_KEY=<your_cosmos_key>" "BLOB_CONNECTION_STRING=<your_storage_connection_string>"

# Deploy lifecycle policy
az storage account blob-service-properties update --account-name $STORAGE_ACCOUNT --resource-group $RESOURCE_GROUP --set lifecycleManagement=@config/blob_lifecycle_policy.json
