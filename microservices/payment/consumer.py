from main import redis, Order
import time

key = 'refund_items'
group = 'payment-group'

try:
  redis.xgroup_create(key, group)
except:
  print('Group already exists!')
  
while True:
  try:
    results = redis.xreadgroup(group, key, {key, '>'}, None)
    if results != []:
      refund_items = []
      
      for result in results:
        obj = result[1][0][1]
        order = Order.get(obj['pk'])
        num_refunded = len(obj) - 1
        if num_refunded == len(order.products):
          order.status('refunded_all')
        else:
          order.status('refunded_partially')
        order.save()
        
  except Exception as e:
    print(str(e))
    
  time.sleep(1)
