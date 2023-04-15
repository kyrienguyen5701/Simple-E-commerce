import os
import requests
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.background import BackgroundTasks
from dotenv import load_dotenv
from redis_om import get_redis_connection, HashModel
from starlette.requests import Request

ROOT = os.path.dirname(__file__)
ENV_PATH = os.path.join(ROOT, '../../.env')
load_dotenv(ENV_PATH)

app = FastAPI()

domain = 'https://example.com'
if os.environ['ENVIRONMENT'] == 'development':
  domain = 'https://localhost'

app.add_middleware(
  CORSMiddleware,
  allow_origins=[f'{domain}:3000'],
  allow_methods=['*'],
  allow_headers=['*']
)

redis = get_redis_connection(
  host=os.environ['PAYMENT_REDIS_HOST'],
  port=int(os.environ['PAYMENT_REDIS_PORT']),
  password=os.environ['PAYMENT_REDIS_PASSWORD'],
  decode_responses=True
)

class Order(HashModel):
  product_IDs: list
  qties: list
  fee: float
  status: str
  
  class Meta:
    database = redis
    
@app.get('/orders/{pk}')
def get(pk: str):
  return Order.get(pk)

@app.post('/orders')
async def create(request: Request, background_tasks: BackgroundTasks):
  body = await request.json()
  product_IDs = body['product_IDs'] # assume that this is the list of product_IDs
  qties = body['qties'] # assume that this is the list of quantities for the products above
  fee = 0
  
  for pID, qty in zip(product_IDs, qties):
    req = requests.get(f'{domain}:8000/products/{pID}')
    product = req.json()
    fee += product['price'] * qty
  
  order = Order(product_IDs, qties, fee, 'pending')
  order.save()
  
  # update the order status
  background_tasks.add_task(order_completed, order)
  
  return order

def order_completed(order: Order):
  time.sleep(5)
  order.status = 'completed'
  order.save()
  
  # Use redis stream to update inventory
  redis.xadd('order_completed', order.dict(), '*')