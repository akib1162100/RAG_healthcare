# RAG Integration Controller — Odoo Module

**Version**: 16.0.1.0.0  
**Category**: Healthcare/Medical  
**Author**: Clidram  
**License**: LGPL-3

## Overview

This Odoo module integrates **Odoo 16** with an external **FastAPI RAG (Retrieval-Augmented Generation)** system for intelligent medical record querying. It enables healthcare professionals to ask natural language questions about patient histories, prescriptions, and medical records directly from Odoo Discuss.

### Key Features

- 🤖 **RAG Bot in Discuss** — AI medical assistant that responds to messages in Odoo Discuss channels
- 💬 **Configurable Chat History** — Admin-controlled context depth for multi-turn conversations
- 🗃️ **Persistent Chat Storage** — All conversations stored in Odoo's PostgreSQL database
- 🔄 **ETL Sync** — Bulk endpoints for syncing prescriptions, patients, appointments, and diseases
- ⚙️ **Centralized Settings** — All configuration in Settings → Healthcare RAG

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│                   ODOO 16                        │
│                                                  │
│  ┌──────────────┐   ┌──────────────────────┐    │
│  │   Settings    │   │   Odoo Discuss       │    │
│  │ ─────────────│   │ ──────────────────── │    │
│  │ • API URL     │   │ User sends message   │    │
│  │ • API Key     │   │       │               │    │
│  │ • Bot Partner │   │       ▼               │    │
│  │ • Context     │   │ mail_channel_inherit  │    │
│  │   Limit (N)   │   │   │                   │    │
│  └──────────────┘   │   ├─ Save to DB        │    │
│                      │   ├─ Fetch last N msgs │    │
│  ┌──────────────┐   │   ├─ Call RAG API      │    │
│  │ rag.chat.    │◄──│   ├─ Save response     │    │
│  │ message (DB) │   │   └─ Post in Discuss   │    │
│  └──────────────┘   └──────────────────────┘    │
│                              │                    │
│                    rag_api_client                  │
│                    HTTP POST ──────────────────────┤
└─────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────┐
│              FastAPI RAG Service                  │
│                                                  │
│  /api/v1/rag/chat                                │
│      │                                           │
│      ├─ Embed prompt (ClinicalBERT)              │
│      ├─ Search vector DB (pgvector)              │
│      ├─ Build medical context                    │
│      ├─ Prepend chat_history to prompt           │
│      └─ Generate answer (Google Gemini)          │
└─────────────────────────────────────────────────┘
```

---

## Module Structure

```
rag_controller/
├── __init__.py
├── __manifest__.py
├── controllers/
│   ├── __init__.py
│   └── main.py                     # HTTP/JSON-RPC API endpoints
├── data/
│   └── rag_bot_data.xml            # Default RAG bot partner record
├── models/
│   ├── __init__.py
│   ├── mail_channel_inherit.py     # Discuss integration (message interception)
│   ├── medical_models_inherit.py   # is_rag_synced field for ETL
│   ├── rag_api_client.py           # HTTP client for FastAPI communication
│   ├── rag_chat_message.py         # Chat history persistence model
│   ├── res_config_settings.py      # Admin settings (URL, key, limit)
│   └── res_partner_inherit.py      # Partner type extensions
├── security/
│   └── ir.model.access.csv         # Access rules for rag.chat.message
└── views/
    ├── res_config_settings_views.xml   # Settings UI
    └── res_partner_inherit_views.xml   # Partner views
```

---

## Configuration

### Settings → Healthcare RAG Integration

| Setting | Description | Default |
|---------|-------------|---------|
| **RAG API Base URL** | FastAPI server URL (e.g., `http://localhost:8000`) | — |
| **RAG API Key** | Bearer token for FastAPI authentication | — |
| **RAG Bot Avatar** | Odoo Contact used as the AI assistant in Discuss | — |
| **Chat History Context Limit** | Number of previous messages to include as context (0 = none) | **3** |

### Chat History Context Limit — Behavior

| Value | Description |
|-------|-------------|
| `0` | No previous context. Each message is independent. |
| `3` | Last 3 messages (user + assistant) sent as context. |
| `5` | Last 5 messages for deeper conversation awareness. |
| `10+` | Extended history for complex medical consultations. |

---

## Data Models

### `rag.chat.message`

Stores every chat message exchanged between users and the RAG assistant.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `channel_id` | Many2one → `mail.channel` | No | The Discuss channel |
| `session_id` | Char (indexed) | Yes | Session identifier (e.g., `odoo_channel_42`) |
| `role` | Selection: `user` / `assistant` | Yes | Message sender |
| `content` | Text | Yes | Raw message text |
| `patient_seq` | Char | No | Patient context (e.g., `20250800494012`) |
| `create_date` | Datetime (auto) | Auto | Message timestamp |

---

## API Endpoints

### Chat Endpoints

| Route | Auth | Description |
|-------|------|-------------|
| `POST /api/rag/chat` | `user` | Conversational RAG with chat history |
| `POST /api/rag/query_patient` | `user` | Query patient-specific data |
| `POST /api/rag/query_prescriptions` | `user` | Search prescriptions |

### ETL / Sync Endpoints

| Route | Auth | Description |
|-------|------|-------------|
| `POST /api/rag/prescriptions/fetch_all` | `public` + API key | Bulk fetch prescriptions |
| `POST /api/rag/patients/fetch_all` | `public` + API key | Bulk fetch patients |
| `POST /api/rag/appointments/fetch_all` | `public` + API key | Bulk fetch appointments |
| `POST /api/rag/diseases/fetch_all` | `public` + API key | Bulk fetch diseases |
| `POST /api/rag/mark_synced` | `public` + API key | Mark records as synced |
| `POST /api/rag/trigger_indexing` | `user` (admin) | Trigger ETL indexing |
| `GET /api/rag/status` | `user` | Get indexing status |

---

## Chat Flow — How It Works

1. **User sends a message** in an Odoo Discuss channel where the RAG Bot is a member
2. `mail_channel_inherit._notify_thread()` intercepts the message
3. A **background thread** is spawned to avoid blocking the UI
4. The user's message is **saved to `rag.chat.message`** with `role='user'`
5. The **last N messages** are retrieved from the database (N = `context_message_limit`)
6. A `chat_history` array is built: `[{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]`
7. The payload (`prompt` + `chat_history`) is sent to the **FastAPI RAG service**
8. FastAPI:
   - Generates an embedding for the prompt
   - Retrieves similar medical documents from the vector database
   - Builds a structured prompt with system instruction + medical context + conversation history
   - Sends to Google Gemini for answer generation
9. The response is **saved to `rag.chat.message`** with `role='assistant'`
10. The formatted response is **posted back into the Discuss channel**

---

## Dependencies

| Module | Purpose |
|--------|---------|
| `base` | Core Odoo |
| `web` | Web framework |
| `mail` | Discuss / messaging |
| `tus_meta_whatsapp_base` | WhatsApp integration base |
| `pos_prescription_knk` | Prescription data model |
| `wk_appointment` | Appointment data model |

---

## Installation

1. Place the `rag_controller` folder in your Odoo addons directory
2. Update the module list: **Settings → Apps → Update Apps List**
3. Install "RAG Integration Controller"
4. Configure settings at **Settings → Healthcare RAG Integration**
5. Ensure the FastAPI RAG service is running and accessible

### Upgrading

After code changes, restart Odoo with:
```bash
python odoo-bin -u rag_controller -d your_database
```

---

## Troubleshooting

| Issue | Solution |
|-------|---------|
| Bot doesn't respond | Verify the RAG Bot Partner is set in Settings and is a member of the channel |
| "RAG API URL not configured" | Set the FastAPI URL in Settings → Healthcare RAG |
| No context in follow-ups | Check `context_message_limit` > 0 in Settings |
| Missing `rag_chat_message` table | Run `-u rag_controller` to apply migrations |
| Access denied errors | Verify `ir.model.access.csv` is loaded (check Settings → Technical → Access Rights) |
