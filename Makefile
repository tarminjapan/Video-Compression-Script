.PHONY: install dev

install:
	uv sync --extra dev
	cd frontend && npm install

dev: install
	cd frontend && npm run electron:dev
