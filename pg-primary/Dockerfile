FROM postgres:16

COPY init.sql               /docker-entrypoint-initdb.d/01-init.sql
COPY setup-replication.sh   /docker-entrypoint-initdb.d/00-setup-replication.sh
COPY postgresql.conf        /etc/postgresql/custom.conf

RUN chmod +x /docker-entrypoint-initdb.d/00-setup-replication.sh

CMD ["postgres", "-c", "config_file=/etc/postgresql/custom.conf"]