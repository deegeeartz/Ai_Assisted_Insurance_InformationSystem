# Widget Dockerfile
# Widget might act differently (embeddable script), but we can serve it as static files too.
# The 'dist' will contain the JS bundle entry point.

FROM node:18-alpine as build

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .
RUN npm run build

# Production Stage
FROM nginx:alpine

# Copy built assets
COPY --from=build /app/dist /usr/share/nginx/html

# Functionally allow CORS so other sites can fetch the script
RUN echo 'server { \
    listen 80; \
    add_header Access-Control-Allow-Origin *; \
    location / { \
    root /usr/share/nginx/html; \
    index index.html index.htm; \
    try_files $uri $uri/ /index.html; \
    } \
    }' > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
