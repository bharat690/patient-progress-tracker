# Patient Progress Tracker

FastAPI backend for longitudinal patient records, document processing, and
record-grounded question answering.

## Local configuration

Copy `.env.example` to `.env`, then set the database, Neo4j, AI-provider, and
object-storage credentials for your environment. Never commit `.env` or place
production secrets in source control. For production, set `APP_ENV=production`
and provide a random `JWT_SECRET_KEY` of at least 32 characters.

## Database migration

Apply database migrations before deploying the application:

```powershell
alembic upgrade head
```

## Authentication

Authentication uses Google Identity Services. Configure `GOOGLE_CLIENT_ID`
on the backend and the matching `VITE_GOOGLE_CLIENT_ID` on the frontend. The
Google OAuth web client must allow the frontend origins used in production and
local development.

The backend verifies Google's signed ID token and creates a doctor account on
first sign-in. Existing accounts are linked by verified email, preserving
their patient records and user IDs. Password registration and login are no
longer accepted.

Authenticated clients send the issued application token as a Bearer token to
protected patient and document endpoints.

## Security configuration

Rate limits and request bounds are configurable with `RAG_RATE_LIMIT`,
`UPLOAD_RATE_LIMIT`, `LOGIN_RATE_LIMIT`, `MAX_QUESTION_LENGTH`, and
`MAX_UPLOAD_BYTES`. The current rate limiter is in-process; multi-worker or
multi-instance deployments need a shared rate-limit store before production
traffic is enabled.
