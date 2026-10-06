FROM nginxinc/nginx-unprivileged:alpine
ENV API_URL=http://api:8000
COPY index.html /usr/share/nginx/html/index.html
COPY default.conf.template /etc/nginx/templates/default.conf.template
EXPOSE 8080
