import json
import os
import time
import redis

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

print("Starting background order worker...")
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

def process_orders():
    while True:
        try:
            # Block and wait for items in the "order_queue" list (timeout after 5 seconds)
            queue_item = redis_client.blpop("order_queue", timeout=5)
            
            if queue_item:
                _, raw_data = queue_item
                order = json.loads(raw_data)
                
                print(f"[PROCESSING] Starting fulfillment for Order ID: {order['order_id']}...")
                time.sleep(3) # Simulate heavy backend processing / cloud DB write
                print(f"[COMPLETED] Successfully processed {order['quantity']}x {order['item_name']} for {order['customer_email']}\n")
                
        except Exception as e:
            print(f"[ERROR] Worker encountered an issue: {e}")
            time.sleep(2)

if __name__ == "__main__":
    process_orders()