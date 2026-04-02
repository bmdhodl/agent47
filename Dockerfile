FROM node:22-alpine AS build

WORKDIR /app/mcp-server

COPY mcp-server/package*.json ./
RUN npm ci

COPY mcp-server/tsconfig.json ./
COPY mcp-server/src ./src
RUN npm run build

FROM node:22-alpine AS runtime

WORKDIR /app/mcp-server
ENV NODE_ENV=production

COPY mcp-server/package*.json ./
RUN npm ci --omit=dev && npm cache clean --force

COPY --from=build /app/mcp-server/dist ./dist

CMD ["node", "/app/mcp-server/dist/index.js"]
