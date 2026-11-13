# ReUseCampus
An AI-Powered Student Marketplace
## Overview
ReUse Campus is a campus-focused student marketplace for discovering and listing second-hand campus essentials such as textbooks, calculators, stationery and room items. It includes AI-assisted recommendations to help users discover relevant listings.
## Features
●	Browse and search public listings.
●	Filter listings by supported category and price criteria.
●	Create and manage listings after signing in.
●	Send enquiries and save listings.
●	Receive AI-assisted listing recommendations.
●	Report listings and support authorised moderation.
## Technology Stack
Python, FastAPI, MySQL 8, SQLAlchemy, Alembic, React, Vite and JavaScript, OpenAPI 3.x, pytest, pytest-cov, Playwright, GitHub Actions, Docker and Docker Compose.
## Dataset
The initial dataset is planned to contain fictional listings created by the team. No real student personal data should be included. Any future third-party data or image source will be documented with its licence and permitted use.
## Running the application
Start the application using:

docker compose up --build -d

Check running services using:

docker compose ps

API documentation: http://localhost:8000/docs
Health check: http://localhost:8000/health

The API automatically runs database migrations and loads synthetic demo data during startup.

Run tests using:

docker compose exec api pytest -q

AI recommendations use sentence-transformers/all-MiniLM-L6-v2. The model cache is stored in the persistent Docker volume hf_cache.

MySQL data is stored in the persistent volume mysql_data. Do not use docker compose down -v unless you intend to delete persistent data.
## Team

| Member  | Name | Github     |
|-------|-----|----------|
| 1 | Tarun Kumar | cs26mt012    |
| 2 | Chetan  | Chetan-cs26mt019   |
| 3  | Archit Kumar  | ArchitKumar-020|
## AI and privacy
The AI recommendation feature uses listing and search text needed for relevance ranking. Passwords, private enquiries and personal identifiers are not sent to an external model. Recommendations are suggestions, not guarantees.
