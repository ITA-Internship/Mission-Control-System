FROM node:24-alpine AS frontend-builder

WORKDIR /frontend

COPY frontend/package.json frontend/package-lock.json ./

RUN npm ci

COPY frontend/ ./

ARG VITE_API_BASE_URL=
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

RUN npm run build


FROM nginx:1.27-alpine

COPY deploy/nginx/default.conf /etc/nginx/conf.d/default.conf

COPY --from=frontend-builder \
    /frontend/dist \
    /usr/share/nginx/html

EXPOSE 80