# Real-Time Fraud & Anomaly Detection

End-to-end real-time fraud detection pipeline. Financial transactions flow through Kafka, are windowed and featurized by Spark Structured Streaming, scored by a River online ML model whose state is persisted in Redis, and the predictions are written to ClickHouse for visualization in Grafana.

## Architecture

```
┌──────────────┐    ┌──────────────┐    ┌────────────────┐    ┌─────────┐
│  Transaction │───▶│ Kafka Topic  │───▶│ Spark Streaming│───▶│  Redis  │
│  Source      │    │ transactions │    │ 1h windows     │    │ Features│
└──────────────┘    └──────────────┘    └────────────────┘    └────┬────┘
                                                                   │
                                                                   ▼
┌──────────────┐    ┌──────────────┐    ┌────────────────┐    ┌─────────┐
│  ClickHouse  │◀───│  River model │◀───│  Predictor     │◀───│  Redis  │
│  (history)   │    │  (online)    │    │  (Python)      │    │ (model) │
└──────┬───────┘    └──────────────┘    └────────────────┘    └─────────┘
       │
       ▼
┌──────────────┐
│   Grafana    │  ← live anomaly rate, top suspicious users, etc.
└──────────────┘
```

The two key differences from the clickstream project:

1. **Per-event prediction**: the River model scores each transaction as it arrives (not per micro-batch). Latency budget is ~10 ms.
2. **Persistent state in Redis**: the model's weights, scaler parameters, and the per-user feature windows all live in Redis. The Spark job and the predictor can both restart independently and pick up where they left off.

## Project structure

```
fraud-detection/
├── docker-compose.yml          # kafka, redis, clickhouse, grafana
├── README.md
├── models/
│   ├── __init__.py
│   ├── transaction.py          # Transaction, LabeledTransaction
│   ├── features.py             # UserFeatures (windowed features)
│   └── prediction.py           # PredictionResult
├── sources/
│   ├── __init__.py
│   └── synthetic_source.py     # realistic transactions with fraud signal
├── kafka_io/
│   ├── __init__.py
│   ├── producer.py             # TransactionProducer
│   └── consumer.py             # TransactionConsumer
├── streaming/
│   ├── __init__.py
│   ├── feature_extractor.py    # Spark Structured Streaming with 1h windows
│   └── predictor.py            # River model wrapper
├── storage/
│   ├── __init__.py
│   ├── feature_store.py        # Redis feature read/write
│   ├── model_store.py          # Redis-backed model state
│   └── clickhouse_writer.py    # prediction logger
├── dashboards/
│   └── grafana_dashboard.json  # live anomaly rate panel
├── tests/
│   └── test_models.py
└── main.py                     # entry point
```

## Tech stack

- **Kafka** — stream of transactions, partitioned by `user_id`
- **Spark Structured Streaming** — 1-hour sliding windows, computes per-user features
- **Redis** — feature store (TTL 1h) + River model state
- **River** — true online ML (`learn_one`, `predict_one`)
- **ClickHouse** — columnar history of every prediction
- **Grafana** — live anomaly rate dashboard

## Setup

```bash
cd fraud-detection
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
docker-compose up -d
```

## Running

Two terminals (as in the clickstream project):

```bash
# Terminal 1: Spark feature extractor
./venv/bin/python3 -u streaming/feature_extractor.py

# Terminal 2: River predictor (consumes from Kafka, scores, writes to ClickHouse)
./venv/bin/python3 -u streaming/predictor.py

# Terminal 3: synthetic source
./venv/bin/python3 -u sources/synthetic_source.py
```
