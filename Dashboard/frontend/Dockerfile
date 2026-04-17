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
RUN printf 'server {\n\
    listen 80;\n\
    location / {\n\
        root /usr/share/nginx/html;\n\
        index index.html;\n\
        try_files $uri $uri/ /index.html;\n\
    }\n\
    location /api/ {\n\
        proxy_pass http://connectai-dashboard-backend:8001/;\n\
        proxy_set_header Host $host;\n\
        proxy_set_header X-Real-IP $remote_addr;\n\
    }\n\
}\n' > /etc/nginx/conf.d/default.conf


EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
