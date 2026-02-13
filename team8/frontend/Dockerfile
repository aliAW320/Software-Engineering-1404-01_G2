# team8/frontend/Dockerfile

# build stage
FROM node:20-alpine AS build
WORKDIR /app

ARG VITE_BASE_PATH=/team8
ARG VITE_API_BASE=/team8/api
ENV VITE_BASE_PATH=${VITE_BASE_PATH}
ENV VITE_API_BASE=${VITE_API_BASE}

COPY package.json package-lock.json* ./
RUN npm ci || npm install

COPY . .

# Build with the configured base so assets resolve behind the gateway path
RUN npm run build -- --base=${VITE_BASE_PATH%/}/

# serve stage
FROM nginx:alpine
ARG VITE_BASE_PATH=/team8
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Put the build output under the base path (defaults to /team8)
RUN mkdir -p "/usr/share/nginx/html${VITE_BASE_PATH}"
COPY --from=build /app/dist "/usr/share/nginx/html${VITE_BASE_PATH}"

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
