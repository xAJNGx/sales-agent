# Multi-Tenant Async Sales Agent

A production-ready **multi-tenant conversational sales agent** built with **FastAPI**, **LangGraph**, **MongoDB**, **Pinecone**, **Google Calendar**, **SendGrid**, and **Ollama**.

## Features

- Async FastAPI architecture
- LangGraph conversational workflow
- RAG with Pinecone
- Multi-tenant support (Organization + Branch)
- Google Calendar booking
- SendGrid email notifications
- Async MongoDB (Motor)
- Local LLMs via Ollama
- Tenant-level data isolation

---

## Architecture

```
Client
   │
FastAPI
   │
LangGraph
   │
├── Intent Router
├── RAG
├── Lead Capture
├── Booking
└── Notifications
        │
Google Calendar + SendGrid
```

---

## Project Structure

```
app/
├── agent/
├── core/
├── db/
├── routes/
├── schemas/
├── services/
├── utils/
└── main.py
```

---

## Intent Types

- `info`
- `purchase`
- `booking`
- `reschedule`
- `cancel`
- `chitchat`

The agent maintains conversation state, allowing booking and lead capture flows to continue until completion.

---

## Multi-Tenant

Each request includes:

```json
{
  "orgId": "org_1",
  "branchId": "branch_a"
}
```

Each tenant has its own:

- Pinecone namespace
- MongoDB data
- Google Calendar
- Sender email
- Business configuration

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| API | FastAPI |
| Workflow | LangGraph |
| LLM | Ollama/OPENAI |
| Vector DB | Pinecone |
| Database | MongoDB |
| Calendar | Google Calendar |
| Email | SendGrid |

---

# Setup

### 1. Clone

```bash
git clone <repository-url>
cd project
```

### 2. Install

```bash
uv sync
```

or

```bash
pip install -r requirements.txt
```

### 3. Configure

```bash
cp .env.example .env
```

Fill in the required environment variables.

### 4. Start Ollama

```bash
ollama pull qwen3.5:4b
ollama pull nomic-embed-text
ollama serve
```

### 5. Run MongoDB

```bash
docker run -d \
  --name mongodb \
  -p 27017:27017 \
  mongo:latest
```

### 6. Configure Pinecone

Create an index and set:

```env
PINECONE_API_KEY=
PINECONE_INDEX=
```

### 7. Configure Google Calendar

- Enable Google Calendar API
- Create a Service Account
- Download credentials JSON
- Share your calendar with the service account
- Set:

```env
GOOGLE_SERVICE_ACCOUNT_JSON=
```

### 8. Configure SendGrid

- Verify a sender/domain
- Create an API key

```env
SENDGRID_API_KEY=
FROM_EMAIL=
```

---

## PDF Ingestion

```bash
python app/utils/ingest_pdf.py
```

Documents are embedded and uploaded to the tenant's Pinecone namespace.

---

## Run

```bash
uvicorn app.main:app --reload
```

---

## API

### Health

```
GET /health
```

### Chat

```
POST /chat
```

Example:

```json
{
  "orgId": "org_1",
  "branchId": "branch_a",
  "sessionId": "s1",
  "message": "I'd like to book a demo tomorrow."
}
```

---

## Environment Variables

Check .env.example

## License

MIT License

---

## Author

**Anuj Nanda Gorkhali**

📧 **ajngworks@gmail.com**