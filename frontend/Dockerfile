FROM node:20-slim AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# Build static export
ENV NEXT_PUBLIC_API_URL=http://localhost:8000
RUN npm run build

# Production stage — lightweight static server
FROM node:20-slim

WORKDIR /app

RUN npm install -g serve@14

COPY --from=builder /app/out ./out

EXPOSE 3000

CMD ["serve", "out", "-l", "3000", "-s"]
