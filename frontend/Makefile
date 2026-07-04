.PHONY: setup build dev test lint typecheck clean docker-build docker-run

setup:
	npm ci
	@echo "✅ Frontend dependencies installed"

build: typecheck
	npm run build
	@echo "✅ Frontend built to out/"

dev:
	npm run dev

typecheck:
	npx tsc --noEmit
	@echo "✅ TypeScript check passed"

lint:
	npx eslint . --ext .ts,.tsx
	@echo "✅ Lint passed"

test:
	npx playwright test

clean:
	rm -rf node_modules .next out

docker-build:
	docker build -t clarifin-frontend .

docker-run: docker-build
	docker run -p 3000:3000 clarifin-frontend
