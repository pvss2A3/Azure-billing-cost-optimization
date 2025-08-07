# Azure Billing Records Cost Optimization

This repository provides a solution to optimize costs for a read-heavy Azure Cosmos DB storing billing records, while maintaining data availability and unchanged API contracts. The system archives records older than 3 months to Azure Blob Storage, reducing Cosmos DB storage and throughput costs.

## Problem Statement

The Azure Cosmos DB database stores over 2 million billing records, each up to 300 KB, with most records older than 3 months rarely accessed. The large database size has increased costs significantly. The solution must:
- Optimize costs while ensuring records remain accessible.
- Maintain simplicity and ease of implementation.
- Ensure no data loss and no downtime during the transition.
- Preserve existing API contracts.
- Serve old records with response times in the order of seconds.

## Solution Overview

The proposed solution uses a **tiered storage architecture** to store recent records (≤ 3 months) in Azure Cosmos DB for low-latency access and archive older records (> 3 months) in Azure Blob Storage for cost efficiency. Key components include:

- **Azure Cosmos DB**: Stores hot data (recent records) and a metadata index for archived records.
- **Azure Blob Storage**: Stores cold data in the **Cool** tier (for records 3–12 months old) and **Archive** tier (for records > 12 months).
- **Azure Functions**: Handles data archival (via Cosmos DB change feed) and API requests (routing to Cosmos DB or Blob Storage).
- **Azure Event Grid**: Triggers archival jobs for records older than 3 months.
- **Azure API Management**: Maintains unchanged API contracts (`GET /billing/{id}`, `POST /billing`).
- **Optional Azure Redis Cache**: Caches frequently accessed records to reduce Cosmos DB RU consumption.

### Architecture Diagram

See `docs/architecture_diagram.md` for a Mermaid diagram of the solution.

### How It Works

1. **Data Archival**:
   - A Cosmos DB change feed triggers an Azure Function (`src/archival_function.py`) when records are older than 3 months (based on `created_at` timestamp).
   - The function uploads the record to Blob Storage, calculates a SHA256 checksum for integrity, creates a metadata document in Cosmos DB (with the record’s ID, Blob URI, and checksum), and deletes the original record.
   - Blob Storage uses a lifecycle policy (`config/blob_lifecycle_policy.json`) to transition records to the Cool tier after 90 days and Archive tier after 365 days, with deletion after 7 years for compliance.

2. **Data Retrieval**:
   - The API handler (`src/api_handler.py`) processes read requests. It checks Cosmos DB first for hot data. If not found, it queries the metadata index to retrieve the record from Blob Storage.
   - Retrieval from Blob Storage (Cool tier) takes 1–5 seconds, meeting the latency requirement. The checksum ensures data integrity.

3. **Cost Optimization**:
   - Archiving 75%+ of records (assuming most are > 3 months) reduces Cosmos DB storage and RU costs.
   - Blob Storage’s Cool tier is significantly cheaper than Cosmos DB, and the Archive tier further reduces costs for older records.
   - Cosmos DB uses autoscale throughput to handle variable read loads efficiently.
   - Optional Redis Cache reduces RU consumption for frequent reads.

### Production Considerations

- **Data Integrity**: Checksums validate archived records. Transactions ensure metadata updates are atomic.
- **Latency**: Cool-tier retrievals meet the seconds-order requirement. Archive-tier access (rare) may take longer, mitigated by user notifications or pre-rehydration.
- **Error Handling**:
  - Retry logic for Cosmos DB RU limits and Blob Storage rate limits.
  - Logging to Azure Application Insights for archival failures.
  - Cleanup jobs to reconcile orphaned records.
- **Scalability**: Azure Functions scale out for archival and API loads. Batch processing handles large datasets.
- **Monitoring**: Azure Monitor tracks RU consumption, API latency, and Blob Storage costs. Budget alerts prevent overruns.
- **Compliance**: Blob Storage lifecycle retains records for 7 years.

### Potential Issues & Mitigations

- **Data Consistency**: Partial archival (e.g., Blob upload succeeds but metadata fails) is mitigated by transactional updates and validation checks.
- **Latency Spikes**: Slow Archive-tier retrievals are addressed by preferring the Cool tier and caching frequent records.
- **Cost Overruns**: RU spikes are managed with autoscale and monitoring. Blob retrieval costs are minimized by lifecycle policies.
- **Scalability Limits**: Large archival jobs are batched, with Durable Functions as a fallback for long-running tasks.

## Setup Instructions

1. **Clone the repository**:
   ```bash
   git clone https://github.com/pvss2A3/azure-billing-cost-optimization.git
   cd azure-billing-cost-optimization

2. **Deploy Azure resources:**:
   - Update deploy/deploy_resources.sh with your Cosmos DB key and Blob Storage connection string.
   - Run:
      ```bash
      chmod +x deploy/deploy_resources.sh
      ./deploy/deploy_resources.sh

3. **Deploy Azure Functions**:
   - Deploy `src/archival_function.py` and `src/api_handler.py` to your Function App:
      ```bash
      func azure functionapp publish billing-functions
   
4. **Configure Blob Storage Lifecycle**:
   - Apply `config/blob_lifecycle_policy.json` using the Azure CLI command in `deploy_resources.sh`.

## Repository Structure

   - `/src`: Azure Functions for archival (`archival_function.py`) and API handling (`api_handler.py`).
   - `/config`: Blob Storage lifecycle policy (`blob_lifecycle_policy.json`).
   - `/deploy`: Deployment script (`deploy_resources.sh`).
   - `/docs`: Architecture diagram (`architecture_diagram.md`) and AI conversation log (`ai_conversation_log.md`).
   - `/tests`: Placeholder for unit tests (e.g., checksum validation, API mocks).

## Running Tests

Placeholder tests are in the `/tests` directory. Add unit tests for:
   - Checksum validation during archival/retrieval.
   - Mocked Cosmos DB queries and Blob Storage retrievals.
   
## Monitoring & Maintenance

   - Use Azure Monitor for RU consumption, API latency, and Blob Storage costs.
   - Set up Application Insights for archival failure alerts.
   - Periodically audit archived records for compliance (e.g., 7-year retention).
