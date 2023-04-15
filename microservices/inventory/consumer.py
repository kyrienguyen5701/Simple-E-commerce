from main import redis, Product
import time

key = 'order_completed'
group = 'inventory-group'

try:
  redis.xgroup_create(key, group)
except:
  print('Group already exists!')
  
while True:
  try:
    results = redis.xreadgroup(group, key, {key, '>'}, None)
    if results != []:
      
      for result in results:
        refund_items = []
        order = result[1][0][1]
        for pID, qty in zip(order['product_IDs'], order['qties']):
          product = Product.get(pID)
          
          # Found product => take it out of inventory
          if product:
            product.qty -= int(qty)
            product.save()
            
          # Product not found => refund for this product only
          else:
            refund_items.append((product['name'], qty))
      
        # Send refund event should there are any refunded products
        if len(refund_items) > 0:
          refund_items.append(('order_ID', order['pk']))
          redis.xadd('refund_items', dict(refund_items), '*')
          
  except Exception as e:
    print(str(e))
    
  time.sleep(1)
