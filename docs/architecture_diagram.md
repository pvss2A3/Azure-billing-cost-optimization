```mermaid
graph TD
    A[Client] -->|Read/Write API| B[Azure API Management]
    B --> C[Azure Functions: API Handler]
    C -->|Hot Data up to 3 months| D[Azure Cosmos DB]
    C -->|Cold Data over 3 months| E[Azure Blob Storage]
    D -->|Metadata for Archived Records| C
    D -->|Age-based Trigger| F[Azure Event Grid]
    F -->|Archival Job| G[Azure Functions: Archival]
    G -->|Move to Blob| E
    G -->|Update Metadata| D
    C -->|Optional Cache| H[Azure Redis Cache]

