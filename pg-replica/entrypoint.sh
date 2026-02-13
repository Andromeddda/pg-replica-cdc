#!/bin/bash
set -e

PRIMARY_HOST="${PRIMARY_HOST:-pg-primary}"
REPLICATOR_USER="${REPLICATOR_USER:-replicator}"
REPLICATOR_PASSWORD="${REPLICATOR_PASSWORD:-replicator}"
PGDATA="${PGDATA:-/var/lib/postgresql/data}"

# ---- Wait for primary to be ready ----
echo "[replica] Waiting for primary at ${PRIMARY_HOST}..."
until PGPASSWORD="$REPLICATOR_PASSWORD" pg_isready -h "$PRIMARY_HOST" -U "$REPLICATOR_USER" -q; do
    sleep 1
done
echo "[replica] Primary is ready."

# ---- Base backup ----
# Check if PGDATA is empty (not initialized)
if [ ! -f "$PGDATA/PG_VERSION" ]; then  
    echo "[replica] Taking base backup from primary..."
    rm -rf "$PGDATA"/*

    # Use pg_basebackup to copy data from primary to replica
    # Use PGPASSWORD env var only for this process to avoid password prompt
    # --progress :              show progress bar
    # --wal-method=stream :     stream WAL files during backup for consistency
    # --write-recovery-conf :   automatically create standby.signal and recovery.conf
    # --format=plain :          create a plain directory structure (not tar)
    PGPASSWORD="$REPLICATOR_PASSWORD" pg_basebackup \
        --host "$PRIMARY_HOST" \
        --username "$REPLICATOR_USER" \
        --pgdata "$PGDATA" \
        --progress \
        --wal-method=stream \
        --write-recovery-conf \
        --format=plain

    # Permissions: owner rwx, group 0, others 0
    chmod 0700 "$PGDATA"
    echo "[replica] Base backup complete."
else
    echo "[replica] PGDATA already initialized, skipping base backup."
fi

# ---- Start in hot-standby mode ----
echo "[replica] Starting PostgreSQL in standby mode..."

# Exec as user 'postgres' to run the server, with hot_standby and primary_conninfo settings
exec postgres \
    -c hot_standby=on \
    -c primary_conninfo="host=${PRIMARY_HOST} \
    user=${REPLICATOR_USER} \
    password=${REPLICATOR_PASSWORD}"