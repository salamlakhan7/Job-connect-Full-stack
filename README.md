# Job Connect AI

Job Connect AI is a Django-based job marketplace that connects candidates and employers with authentication, dashboards, job posting, applications, resume upload, real-time chat, and AI-powered career intelligence.

The platform has evolved from a traditional job board into an AI-assisted hiring product. Candidates can upload resumes, receive structured resume analysis, view career readiness insights, generate embeddings, and receive semantic job recommendations powered by ChromaDB and Sentence Transformers.

## Key Features

- Role-based authentication for candidates and employers
- Candidate dashboard, profile management, resume upload, saved jobs, and applications
- Employer dashboard, job posting, job editing, applicant review, and interview scheduling
- Application status tracking
- WebSocket chat with persisted conversations and file attachments
- Media handling for resumes, profile images, and chat uploads
- Django admin support with Jazzmin styling
- Railway-ready deployment configuration

## AI Features

- Resume Intelligence: extracts PDF text and converts resumes into structured JSON with Groq
- Career Analysis: evaluates resume quality, ATS readiness, career readiness, weak sections, suggested improvements, and career paths
- Embedding Infrastructure: generates candidate and job embeddings with `all-MiniLM-L6-v2`
- Vector Store: stores vectors in ChromaDB while Django stores only embedding metadata
- Semantic Job Matching: recommends jobs using ChromaDB similarity plus deterministic reranking
- Explainable Recommendations: returns matched skills, missing skills, score breakdown, confidence, and next steps

## Technology Stack

### Backend

- Python
- Django
- Django Channels
- Daphne / ASGI
- SQLite for local development
- `dj-database-url` for deployment database configuration
- WhiteNoise for static file serving

### AI and Data

- Groq API for LLM-powered resume and career analysis
- `pypdf` for PDF text extraction
- Sentence Transformers with `all-MiniLM-L6-v2`
- ChromaDB for local vector storage

### Frontend

- Django templates
- HTML, CSS, JavaScript
- WebSocket browser APIs for chat

### Deployment

- Railway-compatible configuration
- Gunicorn / Uvicorn / Daphne dependencies
- Redis channel layer support for production WebSockets

## System Architecture

Job Connect AI uses a conventional Django monolith with service-layer boundaries for AI and vector operations.

```text
Browser
  |
  | HTTP / WebSocket
  v
Django views and Channels consumers
  |
  | ORM / service calls
  v
jobs app
  |
  |-- models.py: users, jobs, applications, chat, AI metadata, recommendations
  |-- views.py: page views and JSON endpoints
  |-- consumers.py: WebSocket chat
  |-- services/: AI, parsing, embeddings, vector store, matching
  |
  | SQL
  v
SQLite or deployment database

External services:
  - Groq API for structured AI analysis
  - ChromaDB for vector storage
  - Redis channel layer in production
```

Business logic for AI features is intentionally kept out of views and placed in `jobs/services/`.

## AI Pipeline

### Resume Intelligence

1. Candidate uploads a PDF resume.
2. The original file is stored normally.
3. `resume_parser.py` extracts text from the PDF.
4. `groq_client.py` sends a privacy-safe structured extraction prompt to Groq.
5. Parsed JSON is stored in `ResumeAnalysis`.
6. Upload remains successful even if AI analysis fails.

### Career Analysis

1. Completed `ResumeAnalysis.parsed_data` is used as input.
2. Career prompts generate quality, ATS, readiness, skills, career paths, improvements, and next actions.
3. Deterministic scoring helpers normalize score fields.
4. Results are stored in `CareerAnalysis`.

### Embeddings

1. Candidate embeddings are generated from `ResumeAnalysis.parsed_data` and `CareerAnalysis.analysis_data`.
2. Job embeddings are generated from job title, description, company, location, and derived skills.
3. Hashes prevent unnecessary regeneration.
4. Vectors are stored in ChromaDB.
5. Django stores metadata only, not raw vectors.

### Semantic Job Matching

1. A seeker refreshes recommendations.
2. The system loads the seeker's completed `CandidateEmbedding`.
3. ChromaDB returns semantically similar job vectors.
4. Applied jobs are excluded where possible.
5. Deterministic reranking combines:
   - Semantic similarity: 45%
   - Skill match: 30%
   - Career readiness: 15%
   - ATS score: 10%
6. Recommendation runs and rows are stored in Django.
7. The seeker dashboard displays a compact AI recommended jobs panel.

## Installation Guide

### Prerequisites

- Python 3.10 or newer recommended
- Git
- Virtual environment support
- Optional: Redis for production-style WebSocket testing

### Clone

```bash
git clone https://github.com/salamlakhan7/Job-connect-Full-stack.git
cd Job-connect-Full-stack
```

### Create a virtual environment

Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

macOS/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Apply migrations

```bash
python manage.py migrate
```

### Create an admin user

```bash
python manage.py createsuperuser
```

## Environment Variables

Create a `.env` file or configure these variables in your host platform.

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `SECRET_KEY` | Production: yes | Development fallback in settings | Django signing key |
| `DEBUG` | No | `True` | Enables development behavior |
| `DATABASE_URL` | No | SQLite database | Deployment database connection |
| `REDIS_URL` | Production WebSockets | `redis://localhost:6379` | Redis channel layer when `DEBUG=False` |
| `GROQ_API_KEY` | For AI analysis | Empty | Enables Groq resume and career analysis |
| `GROQ_MODEL` | No | `llama-3.1-8b-instant` | Groq model name |
| `EMBEDDING_MODEL` | No | `all-MiniLM-L6-v2` | Sentence Transformer model |
| `CHROMA_DB_PATH` | No | `./chroma_db` | ChromaDB persistent storage path |

If `GROQ_API_KEY` is missing, resume upload should still work. AI analysis records fail safely.

## Local Development

Run Django checks:

```bash
python manage.py check
```

Run migrations:

```bash
python manage.py migrate
```

Run tests:

```bash
python manage.py test
```

Use Daphne when testing WebSocket chat:

```bash
daphne -b 127.0.0.1 -p 8000 mysite.asgi:application
```

Open:

```text
http://127.0.0.1:8000/
```

## Running the Project

For basic HTTP development:

```bash
python manage.py runserver
```

For the full app including WebSocket chat:

```bash
daphne -b 127.0.0.1 -p 8000 mysite.asgi:application
```

Static files:

```bash
python manage.py collectstatic --noinput
```

## Project Structure

```text
.
├── jobs/
│   ├── consumers.py              # WebSocket chat consumer
│   ├── decorators.py             # Role-based access decorators
│   ├── forms.py                  # Django forms
│   ├── models.py                 # Core marketplace and AI models
│   ├── routing.py                # Channels WebSocket routes
│   ├── services/
│   │   ├── resume_parser.py
│   │   ├── resume_analysis.py
│   │   ├── resume_prompts.py
│   │   ├── career_analysis.py
│   │   ├── career_prompts.py
│   │   ├── career_scoring.py
│   │   ├── groq_client.py
│   │   ├── embedding_client.py
│   │   ├── candidate_embedding.py
│   │   ├── job_embedding.py
│   │   ├── vector_store.py
│   │   ├── job_matching.py
│   │   └── recommendation_explanations.py
│   ├── templates/                # Django templates
│   ├── urls.py                   # App routes
│   └── views.py                  # Page and JSON views
├── mysite/
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── docs/
│   ├── architecture.md
│   ├── api.md
│   └── deployment.md
├── media/                        # Local uploads, ignored by Git
├── staticfiles/                  # Collected static files, ignored by Git
├── chroma_db/                    # Local vector store, ignored by Git
├── manage.py
├── requirements.txt
└── README.md
```

## API Overview

Most routes are session-authenticated Django endpoints. JSON endpoints are protected by login and role checks.

### Authentication and Dashboards

- `GET /login/`
- `POST /login/`
- `GET /logout/`
- `GET /dashboard/`
- `GET /seeker/dashboard/`
- `GET /employer/dashboard/`

### Candidate Profile and AI

- `GET /seeker/profile/`
- `POST /seeker/profile/`
- `GET /seeker/profile/resume-analysis/`
- `GET /seeker/profile/career-analysis/`
- `POST /seeker/profile/career-analysis/refresh/`

### Semantic Recommendations

- `GET /seeker/jobs/recommendations/`
- `POST /seeker/jobs/recommendations/refresh/`
- `GET /seeker/jobs/recommendations/<recommendation_id>/`

### Jobs and Applications

- `GET /jobs/all/`
- `GET /jobs/search/`
- `GET /job/<job_id>/`
- `GET|POST /job/<job_id>/apply/`
- `GET /seeker/applications/`
- `GET /employer/jobs/`
- `GET|POST /employer/job/post/`
- `GET|POST /employer/job/<job_id>/edit/`
- `GET|POST /employer/job/<job_id>/delete/`
- `GET /employer/job/<job_id>/applicants/`

### Chat

- `GET /chat/`
- `GET /chat/start/<application_id>/`
- `GET /chat/job/<job_id>/`
- `POST /chat/upload/`
- `GET /chat/<conversation_id>/`

See [docs/api.md](docs/api.md) for fuller endpoint notes and example payloads.

## README Image Placeholders

Screenshots should be added when the UI is finalized.

### Landing Page

Placeholder: add a screenshot of the public landing page.

### Resume Upload

Placeholder: add a screenshot of candidate resume upload and profile area.

### Career Analysis

Placeholder: add a screenshot of the Career Intelligence panel.

### AI Recommended Jobs

Placeholder: add a screenshot of semantic job recommendations on the seeker dashboard.

## Future Roadmap

- Background AI processing with Celery and Redis
- Embedding and recommendation management commands
- Explicit Chroma distance metric configuration
- Recommendation caching and refresh policies
- Skill synonym normalization
- Semantic job search
- AI cover letter generation
- Interview preparation assistant
- Employer-side AI candidate ranking
- Resume improvement assistant
- Expanded automated test coverage

## Contributing

1. Fork the repository.
2. Create a feature branch.
3. Keep changes scoped and avoid unrelated refactors.
4. Run `python manage.py check` and `python manage.py test`.
5. Open a pull request with a clear summary and verification notes.

## License

No license file is currently included in this repository. Add a license before distributing or reusing this project outside the repository owner's intended scope.
