# API Documentation

Job Connect AI primarily uses Django template views with session authentication. Several AI-related endpoints return JSON for dashboard panels and refresh actions.

Base URL for local development:

```text
http://127.0.0.1:8000
```

## Authentication

Authentication uses Django sessions.

### Login

```http
GET /login/
POST /login/
```

Form fields:

```text
username=<email>
password=<password>
```

Successful login redirects to `/redirect_dashboard/`, then to the correct role dashboard.

### Logout

```http
GET /logout/
```

### Register Seeker

```http
GET /register/seeker/login
POST /register/seeker/login
```

### Register Employer

```http
GET /register/employer/
POST /register/employer/
```

## Dashboards

### Dashboard Redirect

```http
GET /dashboard/
GET /redirect_dashboard/
```

Redirects the authenticated user to the seeker or employer dashboard.

### Seeker Dashboard

```http
GET /seeker/dashboard/
```

Requires a logged-in seeker.

Displays applications, saved jobs, career intelligence, and AI recommended jobs.

### Employer Dashboard

```http
GET /employer/dashboard/
```

Requires a logged-in employer.

## Resume Analysis

### Seeker Profile and Resume Upload

```http
GET /seeker/profile/
POST /seeker/profile/
```

Requires a logged-in seeker.

Multipart form uploads a candidate resume and profile fields. When a resume PDF is uploaded, the system stores the file and attempts AI resume analysis.

Example multipart fields:

```text
resume=<file.pdf>
phone=...
location=...
summary=...
professional_title=...
```

### Resume Analysis Detail

```http
GET /seeker/profile/resume-analysis/
```

Requires a logged-in seeker.

Example response:

```json
{
  "status": "completed",
  "parsed_data": {
    "full_name": "Candidate Name",
    "email": "candidate@example.com",
    "skills": ["Python", "Django"]
  },
  "error_message": "",
  "model_name": "llama-3.1-8b-instant",
  "analyzed_at": "2026-07-03T10:00:00+00:00",
  "updated_at": "2026-07-03T10:00:00+00:00"
}
```

Notes:

- The endpoint is scoped to the logged-in seeker.
- It does not expose another user's analysis.

## Career Analysis

### Career Analysis Detail

```http
GET /seeker/profile/career-analysis/
```

Requires a logged-in seeker.

Example response:

```json
{
  "status": "completed",
  "overall_score": 78,
  "ats_score": 72,
  "readiness_score": 80,
  "analysis_data": {
    "strongest_skills": ["Django", "REST APIs"],
    "missing_skills": ["Docker"],
    "career_paths": ["Backend Developer"],
    "next_actions": ["Add measurable project impact."]
  },
  "error_message": "",
  "model_name": "llama-3.1-8b-instant",
  "prompt_version": "career-analysis-v1",
  "analyzed_at": "2026-07-03T10:00:00+00:00",
  "updated_at": "2026-07-03T10:00:00+00:00"
}
```

### Refresh Career Analysis

```http
POST /seeker/profile/career-analysis/refresh/
```

Requires a logged-in seeker and a completed resume analysis.

Example response:

```json
{
  "status": "completed",
  "overall_score": 78,
  "ats_score": 72,
  "readiness_score": 80,
  "analysis_data": {},
  "error_message": "",
  "model_name": "llama-3.1-8b-instant",
  "prompt_version": "career-analysis-v1",
  "analyzed_at": "2026-07-03T10:00:00+00:00",
  "updated_at": "2026-07-03T10:00:00+00:00"
}
```

## Job Recommendations

Recommendation endpoints are seeker-only and scoped to the logged-in seeker.

### Latest Recommendation Run

```http
GET /seeker/jobs/recommendations/
```

Example response:

```json
{
  "id": 12,
  "status": "completed",
  "total_jobs_considered": 8,
  "error_message": "",
  "started_at": "2026-07-03T10:00:00+00:00",
  "completed_at": "2026-07-03T10:00:02+00:00",
  "created_at": "2026-07-03T10:00:00+00:00",
  "recommendations": [
    {
      "id": 31,
      "rank": 1,
      "job": {
        "id": 5,
        "title": "Backend Developer",
        "company_name": "Example Inc",
        "location": "Remote"
      },
      "final_score": 84,
      "semantic_score": 88,
      "skills_score": 80,
      "readiness_score": 82,
      "ats_score": 75,
      "confidence": "high",
      "explanation_data": {
        "matched_skills": ["django", "python"],
        "missing_skills": ["docker"],
        "score_breakdown": {
          "semantic_score": 88,
          "skills_score": 80,
          "readiness_score": 82,
          "ats_score": 75
        },
        "summary": "This role matches your profile through django, python.",
        "next_steps": ["Strengthen or add evidence for docker before applying."]
      },
      "created_at": "2026-07-03T10:00:02+00:00"
    }
  ]
}
```

### Refresh Recommendations

```http
POST /seeker/jobs/recommendations/refresh/
```

Creates a new recommendation run from the latest completed candidate embedding.

Failure example:

```json
{
  "id": 13,
  "status": "failed",
  "total_jobs_considered": 0,
  "error_message": "Job matching failed: JobMatchingError",
  "started_at": "2026-07-03T10:00:00+00:00",
  "completed_at": "2026-07-03T10:00:00+00:00",
  "created_at": "2026-07-03T10:00:00+00:00",
  "recommendations": []
}
```

### Recommendation Detail

```http
GET /seeker/jobs/recommendations/<recommendation_id>/
```

Returns one recommendation if it belongs to the logged-in seeker.

## Jobs

### Public Job Detail

```http
GET /job/<job_id>/
```

### Search Jobs

```http
GET /jobs/search/?q=<keyword>
GET /search/?q=<keyword>
```

### All Jobs

```http
GET /jobs/all/
```

### Employer Job List

```http
GET /employer/jobs/
```

Requires an employer account.

### Post Job

```http
GET /employer/job/post/
POST /employer/job/post/
```

Requires an employer account.

Example form fields:

```text
company_name=Example Inc
title=Backend Developer
location=Remote
description=Build Django APIs...
```

Posting a job attempts to generate a job embedding. If embedding generation fails, job posting should still succeed.

### Edit Job

```http
GET /employer/job/<job_id>/edit/
POST /employer/job/<job_id>/edit/
```

Requires the owning employer.

### Delete Job

```http
GET /employer/job/<job_id>/delete/
POST /employer/job/<job_id>/delete/
```

Requires the owning employer.

## Applications

### Apply to Job

```http
GET /job/<job_id>/apply/
POST /job/<job_id>/apply/
```

Requires a seeker account.

Example multipart form fields:

```text
resume=<file>
cover_letter=I am interested in this role...
```

### Seeker Applications

```http
GET /seeker/applications/
GET /seeker/applied/
```

Requires a seeker account.

### Employer Applicants

```http
GET /employer/job/<job_id>/applicants/
```

Requires the owning employer.

### Update Application Status

```http
POST /employer/job/<job_id>/applicant/<app_id>/status/
```

Requires employer authorization.

Example form field:

```text
status=shortlisted
```

### Schedule Interview

```http
GET /application/<app_id>/interview/
POST /application/<app_id>/interview/
```

## Saved Jobs

```http
GET /job/<job_id>/save/
GET /job/<job_id>/unsave/
GET /seeker/saved/
GET /saved-jobs/
```

Requires a seeker account.

## Chat

Chat uses Django views for room setup and Django Channels for real-time message transport.

### Chat List

```http
GET /chat/
```

### Start Chat from Application

```http
GET /chat/start/<application_id>/
```

### Start Chat from Job

```http
GET /chat/job/<job_id>/
```

### Chat Room

```http
GET /chat/<conversation_id>/
```

### Upload Chat Attachment

```http
POST /chat/upload/
```

Example multipart field:

```text
file=<attachment>
```

### WebSocket

The project routes chat WebSocket traffic through Channels. Use Daphne locally to exercise WebSocket behavior:

```bash
daphne -b 127.0.0.1 -p 8000 mysite.asgi:application
```

## Error and Access Patterns

- Unauthenticated users are redirected to login for page views.
- JSON endpoints return `403` for invalid roles.
- Missing AI records commonly return `404`.
- Failed AI operations return safe error messages and should not expose private resume text or embeddings.
