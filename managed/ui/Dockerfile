# Two-stage build (design §11): node builds the static bundle, nginx
# serves it under /ui with a boot-time entrypoint rendering runtime
# config from env. managed/server/Dockerfile (the api image) is untouched by
# this file -- zero backend change.

FROM node:22-alpine AS build
WORKDIR /app
# Dependency layer first so source edits do not re-run npm ci.
COPY package.json package-lock.json ./
RUN npm ci
COPY tsconfig.json vite.config.ts index.html ./
COPY src ./src
RUN npm run build

FROM nginx:1.27-alpine
RUN apk add --no-cache gettext

COPY --from=build /app/dist /usr/share/nginx/html/ui
COPY server/nginx.conf /etc/nginx/nginx.conf
COPY server/default.conf.template /etc/nginx/templates/default.conf.template
COPY server/security-headers.conf.template /etc/nginx/templates/security-headers.conf.template
COPY server/entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh \
    && rm -f /etc/nginx/conf.d/default.conf \
    && mkdir -p /tmp/client_temp /tmp/proxy_temp /tmp/fastcgi_temp /tmp/uwsgi_temp /tmp/scgi_temp \
    && chown -R nginx:nginx /usr/share/nginx/html/ui /etc/nginx/conf.d /tmp

USER nginx
EXPOSE 8080
ENTRYPOINT ["/entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
