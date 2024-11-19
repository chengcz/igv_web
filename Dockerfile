FROM centos:7.9.2009

EXPOSE 80

RUN yum install -y epel-release ca-certificates httpd git curl && \
    yum install -y nginx && \
    yum clean all

# RUN curl -fsSL https://rpm.nodesource.com/setup_16.x | bash - && \
#     yum install -y nodejs && \
#     yum clean all

# RUN yum install npm && npm install -g yarn

# RUN git clone https://github.com/igvteam/igv-webapp /opt/igv-webapp && \
#     cd /opt/igv-webapp && \
#     yarn install && \
#     yarn run build

ADD igv-webapp.1.9.0.tar.gz /opt/

RUN rm -rf /usr/share/nginx/html \
    && ln -s /opt/igv-webapp.1.9.0 /usr/share/nginx/html \
    && ln -sf /dev/stdout /var/log/nginx/access.log \
    && ln -sf /dev/stderr /var/log/nginx/error.log

ENTRYPOINT ["/usr/sbin/nginx"]

CMD ["-g" "daemon off;"]
