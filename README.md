# Gemini Backend Clone

This project is a backend system developed using FastAPI, PostgreSQL, and integrated with Google Gemini API and Stripe. It enables user-specific chatrooms, OTP-based login, AI conversations, and subscription handling.

## Table of Contents

- [Features](#features)
- [Architecture Overview](#architecture-overview)
- [Setup and Run](#setup-and-run)
  - [Prerequisites](#prerequisites)
  - [Environment Variables](#environment-variables)
  - [Running with Docker Compose](#running-with-docker-compose)
  - [Running Locally (without Docker)](#running-locally-without-docker)
- [Queue System Explanation](#queue-system-explanation)
- [Gemini API Integration Overview](#gemini-api-integration-overview)
- [Assumptions/Design Decisions](#assumptionsdesign-decisions)
- [How to Test via Postman](#how-to-test-via-postman)
- [Deployment Instructions](#deployment-instructions)
- [API Endpoints](#api-endpoints)

## Features

- **User Authentication:** OTP-based login (mobile number only) with mocked OTP delivery, and JWT token-based authentication.
- **Chatroom Management:** Users can create, list, and view individual chatrooms.
- **Google Gemini API Integration:** AI conversations powered by Gemini, handling user messages and returning AI responses.
- **Message Queue:** Asynchronous handling of Gemini API calls using Celery and Redis.
- **Subscription & Payments:** Stripe integration for two tiers (Basic/Free and Pro/Paid) with webhook handling.
- **Caching:** Redis-based query caching for `GET /chatroom` endpoint to improve performance.
- **Rate Limiting:** Implemented for Basic tier users to limit daily message prompts.
- **Robust API:** Consistent JSON responses, proper HTTP status codes, middleware for token validation and error handling.

## Architecture Overview

The application follows a layered architecture:

- **`app/main.py`**: The main FastAPI application entry point.
- **`app/api`**: Contains the API route definitions, separated by concerns (auth, chatroom, subscription, user).
- **`app/core`**: Core configurations (settings, security utilities like JWT and password hashing, custom exceptions).
- **`app/db`**: Database-related components (SQLAlchemy models, session management, base for declarative models).
- **`app/schemas`**: Pydantic models for request and response data validation.
- **`app/services`**: Business logic layer, encapsulating operations like user management, chatroom operations, OTP handling, Gemini interaction, and payment processing. This promotes separation of concerns and reusability.
- **`app/tasks`**: Celery tasks for asynchronous operations, specifically for offloading Gemini API calls.
- **`app/utils`**: Utility functions like caching with Redis and rate limiting.

**Database:** PostgreSQL is used as the primary data store.
**Caching and Message Queue Broker:** Redis serves as both the cache store and the broker for Celery.
**Asynchronous Processing:** Celery workers process long-running tasks (like Gemini API calls) in the background.

## Setup and Run

### Prerequisites

- Docker and Docker Compose (recommended for easy setup)
- Python 3.9+
- PostgreSQL client (optional, for direct database access)
- Redis client (optional)

### Environment Variables

Create a `.env` file in the root directory of the project based on the `.env.example` file.

```dotenv
POSTGRES_DB=db_kuvaka
POSTGRES_USER=myuser
POSTGRES_PASSWORD=mypassword

DATABASE_URL=postgresql+asyncpg://myuser:mypassword@db:5432/db_kuvaka

SECRET_KEY=supersecretjwtkey123
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

STRIPE_SECRET_KEY=sk_test_dummykey
STRIPE_WEBHOOK_SECRET=whsec_dummywebhook
STRIPE_BASIC_PRODUCT_ID=prod_dummybasic
STRIPE_PRO_PRODUCT_ID=prod_dummypro
STRIPE_PRO_PRICE_ID=price_dummypro

GEMINI_API_KEY=dummy-gemini-api-key