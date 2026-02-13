#!/bin/bash
set -e

# This script runs inside the postgres initdb phase (as postgres user).
# It creates the replication user and opens pg_hba for replication connections.

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-SQL
    CREATE USER replicator WITH REPLICATION ENCRYPTED PASSWORD 'replicator';
SQL

# Allow replication connections from any host (docker network)
echo "host replication replicator 0.0.0.0/0 md5" >> "$PGDATA/pg_hba.conf"

echo "[setup-replication] replicator user created, pg_hba.conf updated."