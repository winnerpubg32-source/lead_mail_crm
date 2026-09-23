# ---------------------------------------------------------------------------
# OutreachOS — developer shortcuts
#   make help    list every target
# ---------------------------------------------------------------------------
.DEFAULT_GOAL := help
COMPOSE ?= docker compose

.PHONY: help up up-workers down logs build rebuild ps migrate makemigrations superuser shell dbshell test test-backend test-frontend lint typecheck format health clean

help: ## Show this help
	@grep -hE '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-18s\033[0m %s\n", $$1, $$2}'

up: ## Start frontend, backend, postgres and redis
	$(COMPOSE) up --build

up-workers: ## Start the stack plus Celery worker and beat
	$(COMPOSE) --profile workers up --build

down: ## Stop the stack (keeps volumes)
	$(COMPOSE) down

clean: ## Stop the stack and delete volumes
	$(COMPOSE) down -v

logs: ## Tail logs for all services
	$(COMPOSE) logs -f --tail=100

ps: ## Show container status
	$(COMPOSE) ps

build: ## Rebuild images without starting
	$(COMPOSE) build

rebuild: ## Rebuild from scratch (no cache)
	$(COMPOSE) build --no-cache

migrate: ## Apply Django migrations inside the backend container
	$(COMPOSE) exec backend python manage.py migrate

makemigrations: ## Create new migrations
	$(COMPOSE) exec backend python manage.py makemigrations

superuser: ## Create a Django admin user
	$(COMPOSE) exec backend python manage.py createsuperuser

shell: ## Django shell
	$(COMPOSE) exec backend python manage.py shell

dbshell: ## PostgreSQL shell
	$(COMPOSE) exec postgres psql -U $${POSTGRES_USER:-outreachos} -d $${POSTGRES_DB:-outreachos}

test: test-backend test-frontend ## Run every test suite

test-backend: ## Run Django tests
	cd backend && .venv/bin/python manage.py test || $(COMPOSE) exec backend python manage.py test

test-frontend: ## Run the frontend test suite
	cd frontend && npm test

lint: ## Lint the frontend
	cd frontend && npm run lint

typecheck: ## Type-check the frontend
	cd frontend && npm run typecheck

health: ## Probe the API health endpoint
	curl -fsS http://localhost:8000/api/health/ && echo
