# RAG Healthcare System API Documentation

The RAG (Retrieval-Augmented Generation) Healthcare System is a standalone FastAPI backend that seamlessly synchronizes with multiple Odoo instances and companies. It embeds medical records (appointments, prescriptions, patients, diseases) and provides AI-powered natural language queries, chat interfaces, and automated patient summarization using Google Gemini.

## 🏗️ Full Systems Architecture Diagram

```mermaid
graph TB
    %% External Interfaces
    subgraph Odoo Ecosystem
        direction TB
        OdooA[Odoo Instance A <br> Company 1 & 2]
        OdooB[Odoo Instance B <br> Company 1]
        
        subgraph Odoo Modules
            RAGControl[RAG Controller Module]
            Clidram[Clidram Medical Module]
        end
        OdooA --- Odoo Modules
        OdooB --- Odoo Modules
    end

    %% Network Boundary
    subgraph Docker Network
        direction TB
        %% RAG Backend
        subgraph RAG Healthcare Backend [FastAPI Backend]
            API[FastAPI Router <br> HTTP Headers: <br> X-Odoo-Instance-ID <br> X-Odoo-Company-ID]
            
            subgraph Services
                ETL[ETL Pipeline & Data Extractor]
                RAGSvc[RAG Service]
                EmbedSvc[Embedding Service]
                LLMSvc[LLM Service]
            end
            
            API --> ETL
            API --> RAGSvc
            ETL --> EmbedSvc
            RAGSvc --> EmbedSvc
            RAGSvc --> LLMSvc
        end

        %% Database
        subgraph Database [PostgreSQL + pgvector]
            VectorDB[(pgvector Tables: <br> - medical_rag_index <br> - patient_rolling_summaries <br> - etl_metadata <br> *Isolated by instance_id & company_id*)]
        end
        
        ETL -->|Store Embeddings| VectorDB
        RAGSvc -->|Vector Semantic Search| VectorDB
    end

    %% External APIs
    subgraph External APIs
        Gemini[Google Gemini API <br> gemma-4-31b-it]
        LocalModel[Local HuggingFace <br> ClinicalBERT]
    end

    %% External Connections
    LLMSvc -->|Prompt & Context| Gemini
    EmbedSvc -.->|If Local Mode| LocalModel
    
    %% Odoo <-> FastAPI Connections
    RAGControl -- 1. Trigger Indexing --> API
    RAGControl -- 5. Ask AI / RAG Query --> API
    ETL -- 3. Fetch Data API (JSON) --> OdooA
```

---

## 🔐 Multi-Tenant Headers

To ensure that queries are completely isolated between different Odoo instances and different operating companies within those instances, the API requires the following HTTP headers on every request:

- `X-Odoo-Instance-ID`: The unique identifier of your Odoo server (default: `"default"`).
- `X-Odoo-Company-ID`: The specific Odoo company ID requesting the data (default: `1`).

---

## 📡 API Endpoints

### 1. RAG & Chat (AI Interfaces)
These endpoints interact directly with the LLM to provide intelligent answers based on the synchronized medical data.

* **`POST /api/v1/rag/query`**
  * **Description**: Performs a one-off Retrieval-Augmented Generation query against the medical database.
  * **Payload**: `{"prompt": "What medications is John taking?", "patient_seq": "PT123"}`
  * **Behavior**: Vectorizes the prompt, searches `pgvector` for related patient chunks matching the instance/company headers, and generates an AI answer using Gemini.

* **`POST /api/v1/rag/chat`**
  * **Description**: A conversational endpoint that maintains session history.
  * **Payload**: `{"prompt": "Does he have allergies?", "session_id": "user123_chat", "patient_seq": "PT123"}`
  * **Behavior**: Automatically appends context from previous questions in the session for seamless follow-ups.

### 2. Patient Summarization
These endpoints utilize the LLM to summarize large volumes of medical history into structured, easy-to-read clinical overviews.

* **`POST /api/v1/rag/rolling-summary`**
  * **Description**: Generates an incremental "rolling" summary of a patient's medical history.
  * **Payload**: `{"patient_seq": "PT123"}`
  * **Behavior**: Useful for patients with extensive histories. It chunks records and rolls them up chronologically to bypass LLM context limits.

* **`POST /api/v1/rag/summary/regenerate/deep`**
  * **Description**: Forces a complete, deep recalculation of a patient's summary.
  * **Payload**: `{"patient_seq": "PT123"}`
  * **Behavior**: Wipes out existing summaries for the patient and regenerates them entirely from the raw vector database chunks.

* **`POST /api/v1/rag/details`**
  * **Description**: Generates an AI-driven detailed explanation of a specific prescription.
  * **Payload**: `{"patient_seq": "PT123", "record_id": 45}`
  * **Behavior**: Focuses specifically on the context of one prescription (dosages, drug interactions).

### 3. ETL & Data Indexing
These endpoints trigger the backend to pull data from Odoo and update the vector database.

* **`POST /api/v1/etl/index-medical`**
  * **Description**: Triggers a synchronization pipeline.
  * **Payload**: `{"models": ["prescription.order.knk", "wk.appointment"], "incremental": true}`
  * **Behavior**: The backend connects to Odoo via HTTP API, fetches new records, generates text embeddings using ClinicalBERT, and stores them in PostgreSQL (`pgvector`) tagged with the correct `company_id`.

* **`GET /api/v1/etl/status`**
  * **Description**: Checks the status of the indexing pipeline.
  * **Behavior**: Returns metrics on how many records have been vectorized and if the pipeline is currently running.

### 4. Raw Data Retrieval (Debug / Internal)
These endpoints allow Odoo to directly query the raw embedded chunks stored in the vector database without triggering the LLM.

* **`GET /api/v1/rag/patient-data`**
  * **Description**: Retrieves raw embedded patient profile records.
* **`GET /api/v1/rag/prescription-data`**
  * **Description**: Retrieves raw embedded prescription chunks.
* **`GET /api/v1/rag/appointment-data`**
  * **Description**: Retrieves raw embedded appointment records.
* **`GET /api/v1/rag/disease-data`**
  * **Description**: Retrieves medical disease reference records.

*(All data retrieval endpoints require the `X-Odoo-Instance-ID` and `X-Odoo-Company-ID` headers to ensure strict multi-tenant data isolation.)*

## ?? Onboarding a New Odoo Instance

The backend seamlessly supports serving multiple Odoo instances from a single deployment. Follow these steps to configure and synchronize a new instance.

### 1. Update the Configuration
The system parses the .env file to know how to connect to various Odoo instances. Open your .env file and define the ODOO_INSTANCES variable as a JSON array of configuration objects. Each object should include an instance_id, url, and an pi_key.

`env
# Example multi-instance configuration in .env
ODOO_INSTANCES='[{"instance_id": "odoo_alpha", "url": "http://alpha-clinic.local:8069", "api_key": "supersecret1"}, {"instance_id": "odoo_beta", "url": "http://beta-hospital.local:8069", "api_key": "supersecret2"}]'
`
*(Restart the FastAPI Docker container after updating the .env file so the new settings take effect).*

### 2. Configure Odoo
Inside the new Odoo instance (e.g., odoo_beta), configure the RAG controller settings so that it points to your centralized FastAPI backend URL. Make sure the controller is configured to attach the X-Odoo-Instance-ID: odoo_beta header to all outgoing webhook/API requests.

### 3. Initial Data Sync
Once configured, you need to pull the historical data from the new Odoo instance into the RAG backend's vector database. You can trigger this directly from the new Odoo instance's UI (if integrated), or manually hit the ETL endpoint:

`ash
curl -X POST "http://localhost:8000/api/v1/etl/index-medical" \
     -H "Content-Type: application/json" \
     -d '{"instance_id": "odoo_beta", "models": ["prescription.order.knk", "wk.appointment", "res.partner", "medical.disease"], "incremental": false}'
`
*(This triggers the ETLPipeline to fetch records using the odoo_beta credentials, generate embeddings, and store them securely tagged with the instance and company IDs).*

### 4. Background Summaries (Optional)
If your new instance requires pre-computed patient rolling summaries, you can trigger background generation jobs per-patient or globally using the summary regeneration endpoints. Ensure you pass the correct multi-tenant headers:

`ash
curl -X POST "http://localhost:8000/api/v1/rag/summary/regenerate/deep" \
     -H "X-Odoo-Instance-ID: odoo_beta" \
     -H "X-Odoo-Company-ID: 1" \
     -H "Content-Type: application/json" \
     -d '{"patient_seq": "PT001"}'
`
This forces the backend LLM (Google Gemini) to process all raw medical chunks for that patient and calculate a structured summary asynchronously in the background.

