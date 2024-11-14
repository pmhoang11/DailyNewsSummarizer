# import config.
# You can change the default config with `make cnf="config_special.env" build`
cnf ?= .env
include $(cnf)
export $(shell sed 's/=.*//' $(cnf))

VERSION=$(shell cat VERSION)

# HELP
# This will output the help for each task
.PHONY: help

help: ## This help.
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

.DEFAULT_GOAL := help

# DOCKER TASKS
# Build image
build-base: ## Build base image
	docker build --build-arg ENV=$(ENV) -t daily-news-summarizer:base-$(ENV) -f docker/DockerfileBase .

build:
	docker compose -f docker/dev/docker-compose.yml build --build-arg ENV=$(ENV)

# Start
start: ## Start app service
	docker compose -f docker/dev/docker-compose.yml up -d

# Stop
stop: ## Stop app service
	docker compose -f docker/dev/docker-compose.yml down