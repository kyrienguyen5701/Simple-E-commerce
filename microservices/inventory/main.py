import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from redis_om import get_redis_connection, HashModel

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
  host=os.environ['INVENTORY_REDIS_HOST'],
  port=int(os.environ['INVENTORY_REDIS_PORT']),
  password=os.environ['INVENTORY_REDIS_PASSWORD'],
  decode_responses=True
)

class Product(HashModel):
  name: str
  price: float
  qty: int
  
  class Meta:
    database = redis
    
def format(pk: str):
  product = Product.get(pk)
  
  return {
    'id': product.pk,
    'name': product.name,
    'price': product.price,
    'qty': product.qty,
  }

@app.get('/products')
def all():
  return [format(pk) for pk in Product.all_pks()]

@app.get('/products/{pk}')
def get(pk: str):
  return format(pk)

@app.post('/products')
def create(product: Product):
  return product.save()

@app.delete('/products/{pk}')
def remove(pk: str):
  return Product.delete(pk)
