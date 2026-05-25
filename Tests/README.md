# RAG Healthcare System for Odoo 16

A Retrieval-Augmented Generation (RAG) system built specifically for medical/healthcare data in Odoo 16, using **ClinicalBERT** embeddings and **pgvector** for semantic search.

## 🏥 Overview

This system enables natural language queries over Odoo medical records, including:
- Patient appointments
- Prescription orders with medications
- Diagnoses and ICD codes
- Medical history and investigations
- Vital signs and clinical notes

## 🚀 Features

- **Medical-Specific Embeddings**: Uses ClinicalBERT (trained on 2M+ clinical notes) for better understanding of medical terminology
- **Vector Search**: pgvector extension for fast similarity search
- **ETL Pipeline**: Automated extraction, transformation, and loading of Odoo medical data
- **Incremental Indexing**: Only process new/modified records
- **Metadata Filtering**: Query by patient, physician, diagnosis code, medication, date range
- **REST API**: FastAPI endpoints for indexing and querying

## 📋 Prerequisites

- Docker & Docker Compose
- Odoo 16 with Clidram medical modules
- PostgreSQL database with Odoo data
- Python 3.10+

## 🛠️ Installation

### 1. Clone and Setup

```bash
cd P:\RAG_healthcare
cp .env.example .env
# Edit .env with your Odoo database credentials
```

### 2. Configure Environment

Edit `.env` file:

```env
# Odoo Database Connection
ODOO_DB_HOST=your_odoo_host
ODOO_DB_PORT=5432
ODOO_DB_NAME=odoo
ODOO_DB_USER=odoo
ODOO_DB_PASSWORD=your_password

# Embedding Model (ClinicalBERT)
EMBEDDING_MODEL=emilyalsentzer/Bio_ClinicalBERT
EMBEDDING_DIM=768
```

### 3. Start Services

```bash
docker-compose up -d
```

This will start:
- **rag-service**: FastAPI application (port 8000)
- **db**: PostgreSQL with pgvector (port 5432)
- **ollama**: Local LLM service (port 11434)

### 4. Initialize Database

The `database/init_pgvector.sql` script will automatically:
- Enable pgvector extension
- Create `medical_rag_index` table
- Create indexes for performance
- Set up ETL metadata tracking

## 📊 Data Models

### Odoo Models Indexed

| Model | Table | Description |
|-------|-------|-------------|
| `wk.appointment` | `wk_appointment` | Patient appointments |
| `prescription.order.knk` | `prescription_order_knk` | Prescriptions with medications |
| `res.partner` | `res_partner` | Patients and physicians |

### Supporting Data

- **Diagnoses**: ICD codes and disease names
- **Medications**: Dosage, frequency, route, duration
- **Complaints**: Chief complaints with period and location
- **Investigations**: Lab tests and results
- **Vital Signs**: BP, temperature, pulse, etc.

## 🔧 Usage

### API Endpoints

#### 1. Index Medical Data

```bash
curl -X POST http://localhost:8000/index-medical \
  -H "Content-Type: application/json" \
  -d '{
    "models": ["wk.appointment", "prescription.order.knk"],
    "incremental": true,
    "limit": 100
  }'
```

**Response:**
```json
{
  "status": "success",
  "results": {
    "wk.appointment": {
      "records_indexed": 50,
      "chunks_created": 50
    },
    "prescription.order.knk": {
      "records_indexed": 30,
      "chunks_created": 75
    }
  },
  "total_records": 80,
  "total_chunks": 125
}
```

#### 2. Query Patient History

```bash
curl -X POST http://localhost:8000/query-patient \
  -H "Content-Type: application/json" \
  -d '{
    "patient_seq": "202402001",
    "prompt": "What medications has this patient been prescribed?",
    "limit": 5
  }'
```

#### 3. Search Prescriptions

```bash
curl -X POST http://localhost:8000/query-prescriptions \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Find prescriptions for diabetes",
    "diagnosis_code": "E11",
    "date_from": "2024-01-01",
    "limit": 10
  }'
```

#### 4. Check Index Status

```bash
curl http://localhost:8000/index-status
```

**Response:**
```json
{
  "index_stats": {
    "wk.appointment": {
      "total_chunks": 150,
      "unique_records": 150,
      "last_updated": "2024-02-11T10:30:00"
    },
    "prescription.order.knk": {
      "total_chunks": 320,
      "unique_records": 180,
      "last_updated": "2024-02-11T10:35:00"
    }
  },
  "total_indexed_records": 330,
  "total_chunks": 470
}
```

### CLI Usage

Run ETL pipeline directly:

```bash
# Index all appointments
docker-compose exec rag-service python -m app.etl.pipeline --model wk.appointment

# Index prescriptions from last 30 days
docker-compose exec rag-service python -m app.etl.pipeline --model prescription.order.knk --limit 100

# Full reindex
docker-compose exec rag-service python -m app.etl.pipeline --model all --full-reindex

# Check status
docker-compose exec rag-service python -m app.etl.pipeline --status
```

## 🏗️ Architecture

```
┌─────────────────┐
│   Odoo 16 DB    │
│  (PostgreSQL)   │
└────────┬────────┘
         │
         │ Extract
         ▼
┌─────────────────┐
│  ETL Pipeline   │
│  - Extractor    │
│  - Transformer  │
│  - Embeddings   │
│  - Loader       │
└────────┬────────┘
         │
         │ Load
         ▼
┌─────────────────┐
│ medical_rag_    │
│     index       │
│  (pgvector)     │
└────────┬────────┘
         │
         │ Query
         ▼
┌─────────────────┐
│   RAG Engine    │
│  + LlamaIndex   │
│  + Ollama LLM   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   FastAPI       │
│   Endpoints     │
└─────────────────┘
```

## 📁 Project Structure

```
RAG_healthcare/
├── app/
│   ├── etl/
│   │   ├── __init__.py
│   │   ├── odoo_schema.py          # Odoo model mappings
│   │   ├── data_extractor.py       # SQL queries for extraction
│   │   ├── data_transformer.py     # Natural language conversion
│   │   ├── embedding_generator.py  # ClinicalBERT embeddings
│   │   ├── vector_loader.py        # Load to pgvector
│   │   └── pipeline.py             # ETL orchestrator
│   ├── models/
│   │   └── medical_rag.py          # Pydantic models
│   ├── main.py                     # FastAPI application
│   ├── rag_engine.py               # RAG query engine
│   └── database.py                 # Database connections
├── database/
│   └── init_pgvector.sql           # Database initialization
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
└── README.md
```

## 🔬 Embedding Model

**ClinicalBERT** (`emilyalsentzer/Bio_ClinicalBERT`)
- Pre-trained on MIMIC-III clinical notes (2M+ documents)
- Understands medical terminology and abbreviations
- 768-dimensional embeddings
- 512 token max length

**Alternative Models:**
- `pritamdeka/S-PubMedBert-MS-MARCO` - Optimized for medical retrieval
- `microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract` - PubMed trained
- `BAAI/bge-m3` - General purpose (1024 dims, 8192 tokens)

## ⚙️ Configuration

### ETL Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `ETL_BATCH_SIZE` | 32 | Batch size for embedding generation |
| `ETL_CHUNK_SIZE` | 800 | Characters per chunk |
| `ETL_CHUNK_OVERLAP` | 150 | Overlap between chunks |

### Chunking Strategy

- **Appointments**: Usually <512 tokens, no chunking
- **Prescriptions**: Chunked by sections:
  - Chunk 1: Patient info + Diagnosis
  - Chunk 2: Medications
  - Chunk 3: Investigations + History
  - Chunk 4: Procedures + Follow-up

## 🧪 Testing

```bash
# Test database connection
docker-compose exec db psql -U odoo -d odoo -c "SELECT * FROM pg_extension WHERE extname='vector';"

# Test table creation
docker-compose exec db psql -U odoo -d odoo -c "\d medical_rag_index"

# Test API health
curl http://localhost:8000/health

# Index sample data
curl -X POST http://localhost:8000/index-medical \
  -H "Content-Type: application/json" \
  -d '{"models": ["wk.appointment"], "limit": 10}'
```

## 🔒 Security & Privacy

> **⚠️ IMPORTANT**: This system handles sensitive medical data (PHI/PII)

- Use SSL/TLS for all database connections
- Implement proper access controls on API endpoints
- Consider anonymizing patient data in embeddings
- Ensure HIPAA/GDPR compliance
- Audit all queries for regulatory compliance

## 📈 Performance

- **Indexing**: ~100 records/minute (depends on hardware)
- **Query Latency**: <1s for most queries
- **HNSW Index**: Optimized for 768-dim vectors (m=16, ef_construction=64)

## 🐛 Troubleshooting

### Database Connection Issues

```bash
# Check database is running
docker-compose ps db

# Check connection
docker-compose exec rag-service python -c "from app.database import DATABASE_URL; print(DATABASE_URL)"
```

### Embedding Model Download

First run will download ClinicalBERT (~400MB):

```bash
# Check download progress
docker-compose logs -f rag-service
```

### Memory Issues

ClinicalBERT requires ~2GB RAM. If running out of memory:

```bash
# Reduce batch size
export ETL_BATCH_SIZE=16
```

## 📝 License

This project is for internal use with Odoo 16 Clidram medical system.

## 🤝 Contributing

For questions or issues, contact the development team.

---

**Built with**: FastAPI • LlamaIndex • ClinicalBERT • pgvector • Ollama
