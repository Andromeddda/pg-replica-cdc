# Part 1 - Replication


### Architecture
```
┌──────────────┐                   ┌──────────────┐
│  PostgreSQL  │ ────────────────► │  PostgreSQL  │
│   Primary    │    WAL stream     │   Replica    │
│  (port 5432) │                   │  (port 5433) │
└──────┬───────┘                   └──────────────┘
       │
       │ WAL (logical)
       ▼
┌──────────────┐     CDC events    ┌──────────────┐
│   Debezium   │ ────────────────► │    Kafka     │
│  Connect     │                   │ (port 9092)  │
│  (port 8083) │                   └──────┬───────┘
└──────────────┘                          │
                                          ▼
                                  ┌─────────────────┐
                                  │ Python Consumer │
                                  └─────────────────┘
                                          │
                                          ▼
                                ┌─────────────────────┐
                                │  PostgreSQL Target  │
                                │  (port 5434)        │
                                │  orders_read        │
                                │  orders_read_2      │
                                └─────────────────────┘
```