# Patient Progress Tracker

FastAPI backend for longitudinal patient records, document processing, and
record-grounded question answering.

## Local configuration

Copy `.env.example` to `.env`, then set the database, Neo4j, AI-provider, and
object-storage credentials for your environment. Never commit `.env` or place
production secrets in source control. For production, set `APP_ENV=production`
and provide a random `JWT_SECRET_KEY` of at least 32 characters.

## Database migration

The auth fields require a database migration. Apply it before deploying the
application:

```powershell
alembic upgrade head
```

Legacy users receive no password from this migration and must register with a
new email or have their account credentials provisioned through a trusted
administrative process.

## Authentication

Create an account with `POST /auth/register`, obtain an access token with
`POST /auth/login`, and send it as `Authorization: Bearer <token>` to protected
patient and document endpoints. User registration always assigns the standard
doctor role; clients cannot select a role.

## Security configuration

Rate limits and request bounds are configurable with `RAG_RATE_LIMIT`,
`UPLOAD_RATE_LIMIT`, `LOGIN_RATE_LIMIT`, `MAX_QUESTION_LENGTH`, and
`MAX_UPLOAD_BYTES`. The current rate limiter is in-process; multi-worker or
multi-instance deployments need a shared rate-limit store before production
traffic is enabled.