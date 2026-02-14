import json
import os
import time
import base64

from confluent_kafka import Consumer, KafkaException, KafkaError
from decimal import Decimal

import psycopg2


# Config

KAFKA_BOOTSTRAP = os.environ["KAFKA_BOOTSTRAP"]
KAFKA_TOPIC     = os.environ["KAFKA_TOPIC"]

TARGET_DB = {
    "host":     os.environ["TARGET_DB_HOST"],
    "port":     os.environ["TARGET_DB_PORT"],
    "dbname":   os.environ["TARGET_DB_NAME"],
    "user":     os.environ["TARGET_DB_USER"],
    "password": os.environ["TARGET_DB_PASSWORD"],
}

RETRIABLE_ERRORS = {
    KafkaError.UNKNOWN_TOPIC_OR_PART,
    KafkaError._UNKNOWN_TOPIC,
}


# DB helpers

def get_db_conn():
    """Retry loop until the target database is reachable."""
    while True:
        try:
            conn = psycopg2.connect(**TARGET_DB)
            conn.autocommit = True
            return conn
        except Exception as exc:
            print(f"[consumer] DB not ready: {exc}  — retrying in 2 s")
            time.sleep(2)


def upsert_orders_read(cur, row):
    cur.execute(
        """
        INSERT INTO orders_read (id, customer, amount, status, created_at, updated_at)
        VALUES (%(id)s, %(customer)s, %(amount)s, %(status)s, %(created_at)s, %(updated_at)s)
        ON CONFLICT (id) DO UPDATE SET
            customer   = EXCLUDED.customer,
            amount     = EXCLUDED.amount,
            status     = EXCLUDED.status,
            created_at = EXCLUDED.created_at,
            updated_at = EXCLUDED.updated_at;
        """,
        row,
    )


def upsert_orders_read_2(cur, row):
    cur.execute(
        """
        INSERT INTO orders_read_2 (id, customer, status)
        VALUES (%(id)s, %(customer)s, %(status)s)
        ON CONFLICT (id) DO UPDATE SET
            customer = EXCLUDED.customer,
            status   = EXCLUDED.status;
        """,
        row,
    )


def delete_order(cur, order_id):
    cur.execute("DELETE FROM orders_read   WHERE id = %s", (order_id,))
    cur.execute("DELETE FROM orders_read_2 WHERE id = %s", (order_id,))


#  Debezium parsing 

def decode_decimal(value, scale=2):
    """
    Debezium encodes NUMERIC/DECIMAL as Base64 bytes
    (Java BigDecimal unscaled value, big-endian).
    """
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    if isinstance(value, str):
        raw = base64.b64decode(value)
        unscaled = int.from_bytes(raw, byteorder="big", signed=True)
        return Decimal(unscaled) / Decimal(10 ** scale)
    return Decimal(str(value))

def to_timestamp(value):
    """Convert Debezium microsecond-epoch to a human-readable timestamp."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(value / 1_000_000))
    return value


def parse_after(payload: dict) -> dict | None:
    """Return a flat row dict from the 'after' field of a Debezium event."""
    after = payload.get("after")
    if after is None:
        return None
    return {
        "id":         after["id"],
        "customer":   after["customer"],
        "amount":     decode_decimal(after["amount"]),
        "status":     after["status"],
        "created_at": to_timestamp(after.get("created_at")),
        "updated_at": to_timestamp(after.get("updated_at")),
    }


#  Main loop 

def main():
    print(f"[consumer] Connecting to Kafka at {KAFKA_BOOTSTRAP}, topic={KAFKA_TOPIC}")

    consumer = Consumer({
        "bootstrap.servers": KAFKA_BOOTSTRAP,
        "group.id":          "orders-consumer-group",
        "auto.offset.reset": "earliest",
    })
    consumer.subscribe([KAFKA_TOPIC])

    conn = get_db_conn()
    cur  = conn.cursor()
    print("[consumer] Ready. Waiting for events...")

    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() in RETRIABLE_ERRORS:
                    print(f"[consumer] Topic not ready, retrying... ({msg.error()})")
                    time.sleep(2)
                    continue
                raise KafkaException(msg.error())

            raw = msg.value()
            if raw is None:
                continue

            value   = json.loads(raw.decode("utf-8"))
            payload = value.get("payload", value)   # handle envelope
            op      = payload.get("op")             # c / u / d / r

            if op in ("c", "u", "r"):
                row = parse_after(payload)
                if row:
                    upsert_orders_read(cur, row)
                    upsert_orders_read_2(cur, row)
                    print(f"[consumer] UPSERT  id={row['id']}  status={row['status']}")

            elif op == "d":
                order_id = (payload.get("before") or {}).get("id")
                if order_id:
                    delete_order(cur, order_id)
                    print(f"[consumer] DELETE  id={order_id}")

            else:
                print(f"[consumer] unknown op='{op}', skipping")

    except KeyboardInterrupt:
        print("[consumer] Shutting down...")
    finally:
        consumer.close()
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()