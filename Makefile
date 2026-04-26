.PHONY: dev

dev:
	uv sync --extra dev
	cd frontend && npm install && npm run electron:dev
