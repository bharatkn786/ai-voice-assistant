# ─────────────────────────────────────────────
#  Dashboard React Frontend  (multi-stage build)
# ─────────────────────────────────────────────

# ── Stage 1: Build the React app ──
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files first for better layer caching
COPY package.json package-lock.json* ./

RUN npm ci --silent

# Copy source code
COPY . .

# Build production bundle
RUN npm run build

# ── Stage 2: Serve with nginx (tiny, ~20 MB final image) ──
FROM nginx:alpine

# Copy built assets from Stage 1
COPY --from=builder /app/build /usr/share/nginx/html

# Optional: override nginx config to handle React Router (SPA)
RUN echo 'server { \
    listen 80; \
    location / { \
        root /usr/share/nginx/html; \
        index index.html; \
        try_files $uri $uri/ /index.html; \
    } \
    # Proxy API calls to dashboard backend (used in production) \
    location /api/ { \
        proxy_pass http://dashboard-backend:8001/; \
        proxy_set_header Host $host; \
        proxy_set_header X-Real-IP $remote_addr; \
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
