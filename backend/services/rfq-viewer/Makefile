# rfq-viewer — local dev commands
#
# Usage:
#   make help                          — list targets
#   make migrate-generate name=add_foo   — generate a new goose migration
#   make up                            — build and start db + migrate + app
#   make down                          — stop and remove containers
#   make restart                       — down + up
#   make logs                          — follow app logs

DOCKER_COMPOSE ?= docker compose
MIGRATIONS_DIR := migrations

.PHONY: help migrate-generate build up down restart logs migrate

help:
	@echo "rfq-viewer targets:"
	@echo "  make migrate-generate name=<name>   generate a new goose migration (migrations/)"
	@echo "  make migrate                      Apply pending migrations"
	@echo "  make build                        Build the rfq-viewer image"
	@echo "  make up                           Start db + migrate + app"
	@echo "  make down                         Stop and remove containers"
	@echo "  make restart                      Restart the stack"
	@echo "  make logs                         Follow rfq-viewer logs"

migrate-generate:
	@test -n "$(name)" || (echo "usage: make migrate-generate name=<migration_name>" && exit 1)
	goose -s -dir $(MIGRATIONS_DIR) create $(name) sql

migrate:
	$(DOCKER_COMPOSE) run --rm migrate

build:
	$(DOCKER_COMPOSE) build

up: build
	$(DOCKER_COMPOSE) up

down:
	$(DOCKER_COMPOSE) down

restart: down up

logs:
	$(DOCKER_COMPOSE) logs -f rfq-viewer
