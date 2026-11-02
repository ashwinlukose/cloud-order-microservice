import json
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import redis

app = FastAPI(title="Order Ingestion API", version="1.0.0")

# Connect to Redis using environment variables (Docker service name)
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

class Order(BaseModel):
    order_id: str
    item_name: str
    quantity: int
    customer_email: str

@app.post("/api/v1/orders")
def create_order(order: Order):
    """
    Accepts an order, stores state, and pushes an event to the Redis message queue.
    """
    try:
        order_data = order.model_dump()
        
        # Push event to a Redis list ("order_queue") for background processing
        redis_client.rpush("order_queue", json.dumps(order_data))
        
        return {
            "status": "success",
            "message": f"Order {order.order_id} received and queued for processing.",
            "data": order_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "healthy"}