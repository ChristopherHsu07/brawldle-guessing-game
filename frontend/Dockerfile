FROM node:20-alpine AS build

WORKDIR /frontend

# Copies package.json and package-lock.json into working directory first
COPY package*.json .

# fast install dependencies (that's what ci is for)
RUN npm ci

COPY . .

# build the frontend
RUN npm run build

# Moves the built frontend to the nginx container
FROM nginx:alpine
COPY --from=build /frontend/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

RUN chown -R nginx:nginx /var/cache/nginx /usr/share/nginx/html && \
    touch /var/run/nginx.pid && \
    chown nginx:nginx /var/run/nginx.pid

USER nginx


EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
