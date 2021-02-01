FROM alpine:3.12.3
ARG APP_NAME
ARG APP_VERSION
ARG SERVER_EXTERNAL_PORT
ARG SERVER_INTERNAL_PORT
ARG CLUSTER_START_PORT
ARG CLUSTER_NUM
ARG REDIS_EXTERNAL_PORT
ARG REDIS_INTERNAL_PORT
ARG REDIS_PASSWORD
ARG SUPERVISOR_CTL_PORT
ARG CWD=/code
ARG SRC=${CWD}/${APP_NAME}
ARG PIP_TRUST_HOST=https://mirrors.aliyun.com
ARG PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple
ENV TZ=Asia/Shanghai
WORKDIR ${CWD}
RUN sed -i.bak "s@http://dl-cdn.alpinelinux.org/@http://mirrors.aliyun.com/@g" /etc/apk/repositories; \
    apk update; \
    apk upgrade; \
    apk add gcc g++ libffi libffi-dev python3 python3-dev nginx nginx-mod-stream redis curl git bash bash-doc bash-completion openssl openssl-dev py3-pip tzdata; \
    addgroup -S ${APP_NAME}; \
    adduser -S -G ${APP_NAME} -H -s /sbin/nologin ${APP_NAME}; \
    ln -snf /usr/local/zoneinfo/${TZ} /etc/localtime; \
    echo ${TZ} > /etc/timezone
COPY . ${SRC}
RUN cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.bak
COPY ./nginx.conf.example /etc/nginx/nginx.conf
RUN sed -i "s/\${SERVER_INTERNAL_PORT}/${SERVER_INTERNAL_PORT}/g" /etc/nginx/nginx.conf
RUN $(which python3) -m pip install --trusted-host ${PIP_TRUST_HOST} --index-url ${PIP_INDEX_URL} --upgrade pip; \
    $(which python3) -m pip install --trusted-host ${PIP_TRUST_HOST} --index-url ${PIP_INDEX_URL} -r ${SRC}/requirements.txt; \
    $(which python3) -m pip install --trusted-host ${PIP_TRUST_HOST} --index-url ${PIP_INDEX_URL} supervisor
RUN if [ ! -d /etc/supervisor ]; then mkdir -p /etc/supervisor; fi; \
    if [ ! -d /etc/supervisor/conf.d ]; then mkdir -p /etc/supervisor/conf.d; fi; \
    if [ ! -d /etc/redis ]; then mkdir -p /etc/redis; fi; \
    if [ -f /etc/supervisor/supervisor.conf ]; then cp /etc/supervisor/supervisor.conf /etc/supervisor/supervisor.conf.bak; fi; \
    if [ -f /etc/redis/redis.conf ]; then cp /etc/redis/redis.conf /etc/redis/redis.conf.bak; fi
COPY ./redis.conf.example /etc/redis/redis.conf
RUN sed -i "s/\${REDIS_INTERNAL_PORT}/${REDIS_INTERNAL_PORT}/g" /etc/redis/redis.conf
RUN sed -i "s#\${SRC}#${SRC}#g" /etc/redis/redis.conf
RUN sed -i "s/\${APP_NAME}/${APP_NAME}/g" /etc/redis/redis.conf
RUN sed -i "s/\${REDIS_PASSWORD}/${REDIS_PASSWORD}/g" /etc/redis/redis.conf
COPY ./supervisor.conf.example /etc/supervisor/supervisor.conf
RUN sed -i "s/\${SUPERVISOR_CTL_PORT}/${SUPERVISOR_CTL_PORT}/g" /etc/supervisor/supervisor.conf
COPY ./tabocco_data_server_supervisor.conf.example /etc/supervisor/conf.d/tabocco_data_server.conf
RUN sed -i "s#\${SRC}#${SRC}#g" /etc/supervisor/conf.d/tabocco_data_server.conf
COPY entrypoint.sh.example ${SRC}/entrypoint.sh
RUN if [ ! -d ${SRC}/logs ]; then mkdir -p ${SRC}/logs; fi; \
    if [ ! -d ${SRC}/temp ]; then mkdir -p ${SRC}/temp; fi; \
    chown -R ${APP_NAME}:${APP_NAME} ${SRC}; \
    chmod +x ${SRC}/entrypoint.sh; \
    ln -s ${SRC}/entrypoint.sh /usr/bin/entrypoint.sh; \
    chmod -R 777 ${SRC}/temp; \
    chmod -R 777 ${SRC}/logs
ENTRYPOINT ["/usr/bin/entrypoint.sh"]