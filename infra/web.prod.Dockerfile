# ── Build stage ──────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

COPY apps/web/package*.json ./
RUN npm ci

COPY apps/web .

# In production, Next.js rewrites are NOT needed because Caddy
# routes /api/* directly to the API container.
# However, during `next build`, pages that call /api at build-time
# need a dummy value so the build doesn't fail.
ENV NEXT_PUBLIC_API_URL=http://api:8000

RUN npm run build

# ── Runtime stage ────────────────────────────────────
FROM node:20-alpine

WORKDIR /app

COPY --from=builder /app/package*.json ./
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/next.config.js ./

EXPOSE 3000

# Production: next start (serves the .next build output)
CMD ["npm", "start"]
