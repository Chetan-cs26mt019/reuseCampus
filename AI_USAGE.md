# AI_USAGE - ReUse Campus

## AI assistants used

- **OpenAI ChatGPT** was used as a development and documentation assistant during the project workflow represented by the team conversations and the submitted project snapshot.

## How the assistant was used

1. **Technical learning and explanation:** clarifying the responsibilities of the React/Vite frontend, FastAPI endpoints, SQLAlchemy models, Alembic migrations, Docker Compose services, and the recommendation pipeline.
2. **Debugging support:** helping interpret terminal output, reason about failed commands, and suggest checks for backend, frontend, and Docker configuration.
3. **Implementation support:** discussing API behaviour, validation, test cases, recommendation signals, and the relationship between routes, services, and database models. Team members reviewed and tested changes before treating them as part of the project.
4. **Documentation:** helping organise the architecture description, test summary, security review, final report, and this usage record.

The production recommendation feature does not call ChatGPT. It uses the local `sentence-transformers/all-MiniLM-L6-v2` model from the backend service.

## Example of an incorrect AI suggestion and how it was caught

During final Docker Compose documentation work, an AI-generated Python script was suggested to insert `pull_policy: build` under the `api` and `frontend` services. The script tried to detect each service block by searching for the next indented YAML line. That boundary check was incorrect and the script stopped with `StopIteration` when it could not find the expected `image:` line inside the incorrectly extracted block.

The team caught the mistake immediately from the traceback and checked the file with `grep`. Because the script wrote the file only after processing both services, the failed run had not changed `compose.yaml`. The edit was then applied with targeted `sed` commands anchored to the exact image names, and `docker compose config -q` was used to validate the result.

This was a useful reminder that AI-generated commands and scripts must be inspected, run on a safe copy where appropriate, and verified by their actual outputs rather than trusted automatically.

## Human review and verification

- AI-generated explanations and commands were checked against the repository, terminal output, and official tool behaviour.
- Backend behaviour was checked with pytest and coverage; Ruff was run for backend linting.
- Frontend changes were checked with ESLint and a Vite production build.
- Docker Compose configuration was validated and the application was started using the Compose stack.
- The team remains responsible for all submitted code, data, security decisions, and documentation.

## Boundaries

- No passwords, access tokens, private enquiry messages, or personal identifiers were intentionally provided to the recommendation model. The recommender runs locally in the backend and uses listing text and marketplace activity signals.
- AI assistance did not replace peer review, test execution, or the team's responsibility to explain the implementation during the viva.
- This record names the AI assistant visible in the documented workflow. The team should add any additional assistants or tools used by other members before final submission.
