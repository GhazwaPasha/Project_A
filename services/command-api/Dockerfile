# Multi-stage build for command-api (Neon-backed journal commands).
# Build: docker build -t accountuitive-command-api ./services/command-api
# Run:  docker run -e DATABASE_URL -e COMMAND_API_SECRET -p 8787:8787 accountuitive-command-api

FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci
COPY tsconfig.json ./
COPY src ./src
RUN npm run build

FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY package.json package-lock.json* ./
RUN npm ci --omit=dev
COPY --from=build /app/dist ./dist
EXPOSE 8787
CMD ["node", "dist/index.js"]
