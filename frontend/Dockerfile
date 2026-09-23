# syntax=docker/dockerfile:1
# ---------------------------------------------------------------------------
# OutreachOS frontend image (React + Vite + TypeScript)
#
# Targets:
#   development (default) — Vite dev server with HMR on :5173
#   production            — static build served by nginx on :80
# ---------------------------------------------------------------------------
FROM node:22-alpine AS base

WORKDIR /app

ENV CI=true

COPY package.json package-lock.json ./

# --- development ------------------------------------------------------------
FROM base AS development

ENV NODE_ENV=development

RUN npm install

COPY . .

EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]

# --- build ------------------------------------------------------------------
FROM base AS build

RUN npm ci

COPY . .

# The API is reached through a relative /api path, proxied by nginx.
# VITE_USE_MOCK_DATA stays true in Phase 1 because the analytics endpoint does
# not exist yet — flip it to "false" once it returns DashboardOverview data.
ENV VITE_API_BASE_URL=/api \
    VITE_USE_MOCK_DATA=true

RUN npm run build

# --- production -------------------------------------------------------------
FROM nginx:1.27-alpine AS production

COPY nginx/default.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD wget -q -O /dev/null http://127.0.0.1/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
