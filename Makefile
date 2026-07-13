# PriceChecker — Docker orchestration
#
# Usage:
#   make help              — list targets
#   make up                — start all stacks
#   make down              — stop all stacks

DOCKER_COMPOSE ?= docker compose
NETWORK        := pricechecker

ROOT_DIR        := $(CURDIR)
ROOT_COMPOSE    := $(ROOT_DIR)/docker-compose.yaml
RFQ_COMPOSE     := $(ROOT_DIR)/backend/services/rfq-service/docker-compose.yml
VIEWER_COMPOSE  := $(ROOT_DIR)/backend/services/rfq-viewer/docker-compose.yml
CRED_COMPOSE    := $(ROOT_DIR)/backend/services/credentials-keeper/docker-compose.yml

DC_ROOT    := $(DOCKER_COMPOSE) -f $(ROOT_COMPOSE)
DC_RFQ     := $(DOCKER_COMPOSE) -f $(RFQ_COMPOSE)
DC_VIEWER  := $(DOCKER_COMPOSE) -f $(VIEWER_COMPOSE)
DC_CRED    := $(DOCKER_COMPOSE) -f $(CRED_COMPOSE)

.PHONY: help network env-check \
	up down \
	app-up app-down app-logs \
	credentials-up credentials-down credentials-logs \
	rfq-up rfq-down rfq-logs rfq-build \
	rfq-listener-up rfq-listener-down rfq-listener-logs \
	rfq-extractor-up rfq-extractor-down rfq-extractor-logs \
	rfq-infra-up rfq-infra-down \
	viewer-up viewer-down viewer-logs viewer-migrate viewer-build

help:
	@echo "PriceChecker Docker targets:"
	@echo ""
	@echo "  All stacks:"
	@echo "    make up                  Start everything (app + RFQ pipeline + viewer)"
	@echo "    make down                Stop everything"
	@echo ""
	@echo "  PriceChecker app (backend + frontend):"
	@echo "    make app-up / app-down / app-logs"
	@echo ""
	@echo "  Credentials Keeper (PostgreSQL only):"
	@echo "    make credentials-up / credentials-down / credentials-logs"
	@echo ""
	@echo "  RFQ pipeline (MinIO + NATS + listener + extractor + viewer):"
	@echo "    make rfq-up / rfq-down / rfq-logs / rfq-build"
	@echo "    make rfq-infra-up              MinIO + NATS only"
	@echo "    make rfq-listener-up           Listener only (needs infra)"
	@echo "    make rfq-extractor-up          Extractor only (needs infra)"
	@echo ""
	@echo "  RFQ Viewer (PostgreSQL + migrations + API):"
	@echo "    make viewer-up / viewer-down / viewer-logs / viewer-migrate"

# ---------------------------------------------------------------------------
# Shared setup
# ---------------------------------------------------------------------------

network:
	@docker network inspect $(NETWORK) >/dev/null 2>&1 \
		|| docker network create $(NETWORK)

env-check:
	@test -f backend/services/rfq-service/listener/.env \
		|| (echo "Missing backend/services/rfq-service/listener/.env — copy from .env.example" && exit 1)
	@test -f backend/services/rfq-service/extractor/.env \
		|| (echo "Missing backend/services/rfq-service/extractor/.env — copy from .env.example" && exit 1)
	@test -f backend/services/rfq-viewer/.env \
		|| (cp backend/services/rfq-viewer/.env.example backend/services/rfq-viewer/.env \
			&& echo "Created backend/services/rfq-viewer/.env from .env.example")

# ---------------------------------------------------------------------------
# All stacks
# ---------------------------------------------------------------------------

up: network env-check app-up rfq-up
	@echo "All services started."

down: viewer-down rfq-down app-down
	@echo "All services stopped."

# ---------------------------------------------------------------------------
# PriceChecker app (root compose: backend + frontend; uses credentials-db from root or credentials stack)
# ---------------------------------------------------------------------------

app-up: network
	$(DC_ROOT) up -d --build

app-down:
	$(DC_ROOT) down

app-logs:
	$(DC_ROOT) logs -f backend frontend

# ---------------------------------------------------------------------------
# Credentials Keeper
# ---------------------------------------------------------------------------

credentials-up: network
	$(DC_CRED) up -d

credentials-down:
	$(DC_CRED) down

credentials-logs:
	$(DC_CRED) logs -f credentials-db

# ---------------------------------------------------------------------------
# RFQ pipeline
# ---------------------------------------------------------------------------

rfq-build: env-check
	$(DC_RFQ) build

rfq-up: network env-check rfq-build rfq-infra-up
	$(DC_RFQ) up -d --build rfq-listener rfq-extractor
	$(MAKE) viewer-up

rfq-down:
	$(DC_RFQ) down

rfq-logs:
	$(DC_RFQ) logs -f rfq-listener rfq-extractor

rfq-infra-up: network
	$(DC_RFQ) up -d minio nats

rfq-infra-down:
	$(DC_RFQ) stop minio nats

rfq-listener-up: network env-check
	$(DC_RFQ) up -d --build minio nats rfq-listener

rfq-listener-down:
	$(DC_RFQ) stop rfq-listener

rfq-listener-logs:
	$(DC_RFQ) logs -f rfq-listener

rfq-extractor-up: network env-check
	$(DC_RFQ) up -d --build minio nats rfq-extractor

rfq-extractor-down:
	$(DC_RFQ) stop rfq-extractor

rfq-extractor-logs:
	$(DC_RFQ) logs -f rfq-extractor

# ---------------------------------------------------------------------------
# RFQ Viewer
# ---------------------------------------------------------------------------

viewer-build: env-check
	$(DC_VIEWER) build

viewer-migrate: network env-check
	$(DC_VIEWER) run --rm migrate

viewer-up: network env-check rfq-infra-up viewer-build
	$(DC_VIEWER) up -d

viewer-down:
	$(DC_VIEWER) down

viewer-logs:
	$(DC_VIEWER) logs -f rfq-viewer
