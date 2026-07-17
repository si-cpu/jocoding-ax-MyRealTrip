FROM node:24-slim AS deps

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

FROM node:24-slim AS builder

WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

RUN apt-get update \
  && apt-get install -y --no-install-recommends python3 \
  && rm -rf /var/lib/apt/lists/*

RUN npm run db:build
RUN npm run build

FROM node:24-slim AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000
ENV HOSTNAME=0.0.0.0

COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/package-lock.json ./package-lock.json
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/data ./data
COPY --from=builder /app/scripts ./scripts

EXPOSE 3000

CMD ["npm", "run", "start"]
