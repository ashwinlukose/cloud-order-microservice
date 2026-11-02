# Cloud Order Microservice

An asynchronous order ingestion and processing microservice architecture built with **FastAPI**, **Redis**, and a **Python Background Worker**, containerized with **Docker Compose**.

---

## Architecture Overview

This project implements an asynchronous producer-consumer pattern to decouple order intake from long-running fulfillment operations:

```
+----------------+          HTTP POST          +-------------------+
|  Client / Web  | --------------------------> |     Order API     |
|   (Postman/    |                             |     (FastAPI)     |
|     cURL)      | <-------------------------- |    Port: 8000     |
+----------------+      200 OK (Queued)        +-------------------+
                                                         |
                                                    RPUSH (Queue)
                                                         v
                                               +-------------------+
                                               |   Redis Broker    |
                                               |  (order_queue)    |
                                               |    Port: 6379     |
                                               +-------------------+
                                                         |
                                                    BLPOP (Poll)
                                                         v
                                               +-------------------+
                                               |   Order Worker    |
                                               | (Python Service)  |
                                               |    Fulfillment    |
                                               +-------------------+
```

### Components

1. **`order-api` (FastAPI)**:
   - High-throughput REST API for ingesting customer orders.
   - Validates incoming order payloads using Pydantic models.
   - Pushes serialized order records to the Redis `order_queue` list and responds immediately to the caller.
   - Exposes interactive OpenAPI documentation and health check endpoints.

2. **`redis` (Redis 7 Alpine)**:
   - In-memory message broker that holds pending orders in a FIFO queue.

3. **`order-worker` (Python Background Worker)**:
   - Lightweight standalone worker utilizing Redis `BLPOP` to consume jobs continuously.
   - Simulates downstream fulfillment processing (e.g., database writes, third-party payment/logistics APIs) without blocking API response times.

---

## Project Structure

```text
cloud-order-microservice/
├── api/
│   ├── Dockerfile             # Multi-stage container definition for FastAPI
│   ├── main.py                # FastAPI endpoints and Redis producer logic
│   └── requirements.txt       # Dependencies: FastAPI, Uvicorn, Pydantic, Redis
├── worker/
│   ├── Dockerfile             # Container definition for worker service
│   ├── requirements.txt       # Dependencies: Redis client
│   └── worker.py              # Background consumer logic using BLPOP
├── docker-compose.yml         # Multi-container orchestration definition
└── README.md                  # Project documentation
```

---

## Prerequisites

- [Docker](https://www.docker.com/) (v20.10+)
- [Docker Compose](https://docs.docker.com/compose/) (v2.0+)

---

## Getting Started

### 1. Clone & Navigate to Project

```bash
git clone <repository-url>
cd cloud-order-microservice
```

### 2. Build and Start Services

Launch the entire stack using Docker Compose:

```bash
docker compose up --build -d
```

Check the status of running containers:

```bash
docker compose ps
```

Expected output:
```text
NAME                       IMAGE                                   STATUS         PORTS
fastapi_order_api          cloud-order-microservice-order-api      Up             0.0.0.0:8000->8000/tcp
python_background_worker   cloud-order-microservice-order-worker   Up             
redis_broker               redis:7-alpine                          Up             0.0.0.0:6379->6379/tcp
```

### 3. View Service Logs

Follow logs in real time:

```bash
# All services
docker compose logs -f

# Worker service only
docker compose logs -f order-worker

# API service only
docker compose logs -f order-api
```

---

## API Reference

### Health Check

- **Endpoint**: `GET /health`
- **Description**: Verifies API operational status.

```bash
curl http://localhost:8000/health
```

**Response (`200 OK`)**:
```json
{
  "status": "healthy"
}
```

---

### Submit Order

- **Endpoint**: `POST /api/v1/orders`
- **Description**: Accepts an order and schedules it for background processing.

#### Request Body
```json
{
  "order_id": "ORD-12345",
  "item_name": "Mechanical Keyboard",
  "quantity": 2,
  "customer_email": "jane.doe@example.com"
}
```

#### Example cURL Command
```bash
curl -X POST http://localhost:8000/api/v1/orders \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "ORD-12345",
    "item_name": "Mechanical Keyboard",
    "quantity": 2,
    "customer_email": "jane.doe@example.com"
  }'
```

**Response (`200 OK`)**:
```json
{
  "status": "success",
  "message": "Order ORD-12345 received and queued for processing.",
  "data": {
    "order_id": "ORD-12345",
    "item_name": "Mechanical Keyboard",
    "quantity": 2,
    "customer_email": "jane.doe@example.com"
  }
}
```

### Interactive Documentation

Once services are running, visit:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## Verifying Asynchronous Processing

1. Open a terminal and watch the worker logs:
   ```bash
   docker compose logs -f order-worker
   ```

2. In another terminal, trigger multiple order submissions:
   ```bash
   curl -s -X POST http://localhost:8000/api/v1/orders \
     -H "Content-Type: application/json" \
     -d '{"order_id": "ORD-101", "item_name": "Wireless Mouse", "quantity": 1, "customer_email": "alice@example.com"}'
   ```

3. Observe the worker terminal consuming the queue items:
   ```text
   Starting background order worker...
   [PROCESSING] Starting fulfillment for Order ID: ORD-101...
   [COMPLETED] Successfully processed 1x Wireless Mouse for alice@example.com
   ```

---

## Configuration & Environment Variables

| Variable | Default | Description | Services |
| :--- | :--- | :--- | :--- |
| `REDIS_HOST` | `redis` (in Docker) / `localhost` | Redis server hostname | `order-api`, `order-worker` |
| `REDIS_PORT` | `6379` | Redis server port | `order-api`, `order-worker` |
| `PYTHONUNBUFFERED` | `1` | Forces unbuffered stdout/stderr output in Docker | `order-api`, `order-worker` |

---

## Stopping the Services

To stop and remove containers and network:

```bash
docker compose down
```

To stop and remove all volumes as well:

```bash
docker compose down -v
```

