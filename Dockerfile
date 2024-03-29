FROM python:3.11-alpine

ARG REQFILE=requirements-dep.txt
ENV APP_HOME=/var/local/scratch

RUN apk add --no-cache --update gcc tzdata postgresql-dev libc-dev linux-headers openldap-dev
RUN ln /usr/lib/libldap.so /usr/lib/libldap_r.so

RUN mkdir -p $APP_HOME

COPY requirements* $APP_HOME/
WORKDIR $APP_HOME

RUN pip install --upgrade pip
RUN pip install --no-cache-dir  -r $REQFILE

COPY . $APP_HOME

ENTRYPOINT ["./docker-entrypoint.sh"]
