# Makefile for Localrun Docker image management

-include .env
export

REGISTRY := ghcr.io
ORG := localrun-tech
IMAGE_NAME := portal
VERSION := latest
PLATFORMS := linux/amd64,linux/arm64

FULL_IMAGE := $(REGISTRY)/$(ORG)/$(IMAGE_NAME):$(VERSION)

.PHONY: help
help:
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

.PHONY: build
build: ## Build Docker image locally for current platform
	docker build -t localrun-portal:latest -t $(FULL_IMAGE) .

.PHONY: test
test: build ## Build and run local test container
	docker run -d \
		--name localrun-test \
		--volume /var/run/docker.sock:/var/run/docker.sock \
		--volume localrun-data:/data/localrun \
		--publish 8000:8000 \
		--publish 3006:3006 \
		localrun-portal:latest

.PHONY: logs
logs: ## Show logs from test container
	docker logs -f localrun-test

.PHONY: clean
clean: ## Clean up local images
	docker rmi localrun-portal:latest 2>/dev/null || true
	docker volume rm localrun-data 2>/dev/null || true

