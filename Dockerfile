FROM ubuntu:24.04

EXPOSE 80

RUN apt update && \
    apt install -y ca-certificates apache2 git curl nginx && \
    apt clean

ADD igv-webapp /opt/

RUN rm -rf /usr/share/nginx/html \
    && ln -s /opt/igv-webapp /usr/share/nginx/html \
    && ln -sf /dev/stdout /var/log/nginx/access.log \
    && ln -sf /dev/stderr /var/log/nginx/error.log

ENTRYPOINT ["/usr/sbin/nginx"]

CMD ["-g" "daemon off;"]
