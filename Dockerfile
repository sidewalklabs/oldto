FROM node:9.8.0-alpine as builder
ARG GMAPS_API_KEY

WORKDIR oldto-site
COPY oldto-site .
ENV GMAPS_API_KEY $GMAPS_API_KEY
RUN yarn && yarn webpack

FROM nginx:1.13.12-alpine

COPY --from=builder oldto-site/dist /usr/share/nginx/html
COPY nginx.config /etc/nginx/conf.d/default.conf

EXPOSE 80
