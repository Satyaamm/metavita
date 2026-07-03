# MetaVita web app (Next.js standalone).
# Build context must be the repo root: docker build -f apps/web/Dockerfile .
FROM node:20-slim AS deps
WORKDIR /app
COPY apps/web/package.json apps/web/package-lock.json* ./
RUN npm install

FROM node:20-slim AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY apps/web ./
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

FROM node:20-slim AS runner
WORKDIR /app
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1
RUN useradd --create-home --uid 10001 appuser
# Next.js standalone output keeps the runtime image small.
COPY --from=build /app/.next/standalone ./
COPY --from=build /app/.next/static ./.next/static
COPY --from=build /app/public ./public
USER appuser
EXPOSE 3000
CMD ["node", "server.js"]
