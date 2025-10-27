# AURELIA — Financial RAG Chatbot (GCP)

This repository contains **Retrieval‑Augmented Generation** system that produces
structured **financial concept notes** with caching, hybrid retrieval, and resilient fallbacks.

**Core stack:** FastAPI (API) • Streamlit (UI) • Pinecone Hybrid (dense + BM25) • OpenAI •
LangChain • PostgreSQL (Cloud SQL) • Airflow (Cloud Composer) • Terraform • GitHub Actions

---

## Demo of the project
https://northeastern-my.sharepoint.com/:v:/g/personal/gandhi_di_northeastern_edu/ESRwBVVekpdHso5hyPUtrJ0BGyJAzNsHbNWipJW1RilofA?e=xu4Ubd&nav=eyJyZWZlcnJhbEluZm8iOnsicmVmZXJyYWxBcHAiOiJTdHJlYW1XZWJBcHAiLCJyZWZlcnJhbFZpZXciOiJTaGFyZURpYWxvZy1MaW5rIiwicmVmZXJyYWxBcHBQbGF0Zm9ybSI6IldlYiIsInJlZmVycmFsTW9kZSI6InZpZXcifX0%3D

## Architecture (Overall System)

![alt text](ArchitectureDiagram.png)

**Key highlights**
- **Cache‑first:** FastAPI checks **Cloud SQL** before doing any model calls; cache hits cut P95 latency & token cost.
- **Hybrid retrieval:** Pinecone combines **dense** (OpenAI `text-embedding-3-large`) + **sparse** (BM25) signals.
- **Structured generation:** Instructor + Pydantic ensures consistent schema with citations & sources.
- **Fallback:** If recall is low, the API leverages **Wikipedia** so users still get an answer (clearly labeled).
- **Orchestration:** **Composer (Airflow)** runs the **Ingest DAG** (index build/update) and **Seed DAG** (pre‑warm cache).
- **IaC & CI/CD:** Terraform provisions GCP; GitHub Actions builds/deploys Cloud Run and syncs DAGs.


## Quick Start (Local)

### 1) Prerequisites
- Python **3.10+**, Docker (optional)
- Accounts/keys: **OpenAI**, **Pinecone** (index created)
- Local Postgres 14+ (or use SQLite for smoke tests)

### 2) Environment
Create `.env` in repo root:
```env
OPENAI_API_KEY=sk-...
PINECONE_API_KEY=pcsk-...
PINECONE_INDEX_NAME=fintbx-hybrid-3072

# Local DB
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/aurelia_db
# or: sqlite:///./aurelia.db
```

### 3) Run
```bash
# API
cd app
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8080

# Frontend (new shell)
cd ../frontend
pip install -r requirements.txt
streamlit run app.py --server.port 8501
```

### 4) Smoke test
```bash
curl -X POST http://localhost:8080/query -H "Content-Type: application/json"   -d '{"concept":"Discounted Cash Flow","force_refresh":false}'
```

---

## Ingestion & Seeding

### Option A — Local helpers
```bash
cd chunking_strategy1
python parser_enhanced_markdown.py
python aurelia_to_langchain.py
python upload_to_pinecone_hybrid.py
```

### Option B — Airflow (Composer)
- **`fintbx_ingest_dag.py`**: parse → chunk → hybrid upload to Pinecone
- **`concept_seed_dag.py`**: call `/query` for a concept list to **pre‑warm the cache**

> Demo note: three green tasks — `validate_api_connection` → `call_seed_endpoint` → `verify_seeding_results` — confirm API health, seed calls, and rows cached in Cloud SQL.

---

## GCP Deployment (Cloud Run + Cloud SQL + Composer)

1. **Build & push images**
```bash
gcloud auth configure-docker
docker build -t gcr.io/$PROJECT/aurelia-api:latest ./app && docker push gcr.io/$PROJECT/aurelia-api:latest
docker build -t gcr.io/$PROJECT/aurelia-ui:latest  ./frontend && docker push gcr.io/$PROJECT/aurelia-ui:latest
```

2. **Terraform**
Create/adjust `terraform/terraform.tfvars`:
```hcl
project_id       = "YOUR_GCP_PROJECT"
region           = "us-east1"
db_instance_name = "aurelia-postgres"
db_user          = "aurelia_user"
db_password      = "CHANGE_ME"
fastapi_image    = "gcr.io/YOUR_GCP_PROJECT/aurelia-api:latest"
frontend_image   = "gcr.io/YOUR_GCP_PROJECT/aurelia-ui:latest"
app_name         = "aurelia"
```
Then:
```bash
cd terraform
terraform init
terraform apply -auto-approve
```

3. **Cloud Run ↔ Cloud SQL**
- Grant the Cloud Run service account **Cloud SQL Client**.
- Use the Unix socket form of `DATABASE_URL` in prod, e.g.  
  `postgresql+pg8000://aurelia_user:${ ' }}DB_PASSWORD{{ ' }@/aurelia_db?host=/cloudsql/${ ' }}DB_CONN_NAME{{ ' }`

4. **DAGs**
- Sync `./dags` to Composer’s bucket (or use `.github/workflows/deploy-dags.yml`).

---

## API Reference

- `GET /health` — dependency check (Pinecone, DB)
- `POST /query` — `{"concept":"<str>", "force_refresh": <bool>}` → structured ConceptNote
- `GET /cache` — list cached concepts
- `DELETE /cache/{concept}` — evict a cached note
- `GET /stats` — basic counters, hit rate

---

## Troubleshooting

- **Empty/weak retrieval** → ensure ingest ran and `PINECONE_INDEX_NAME`/namespace match.
- **High latency** → re-run the **Seed DAG**; confirm cache hits; consider smaller model or turn off reranker.
- **Cloud SQL auth** → check service account roles; verify socket `DATABASE_URL`.
- **Composer imports** → add missing PyPI deps to environment.



