import xmlrpc.client

url = "http://0.0.0.0:8069"
db = "postgres"
username = "admin"
password = "admin"
# username = "arsalan.9798@gmail.com"
# password = "12345"

# Authenticate the user
common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
print("-----comon----", common)
uid = common.authenticate(db, username, password, {})
print("-----user id====", uid, type(uid))

# Connect to the object endpoint
models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
print("-----models----", models)
# Search for sale.order records for the authenticated user
sale_order_ids = models.execute_kw(db, uid, password, 'sale.order', 'search',
                                   [[['user_id', '=', uid]]])
print("-----sale_order-id----", sale_order_ids)
# Read details of the found sale orders
sale_orders = models.execute_kw(db, uid, password, 'sale.order', 'read',
                                [sale_order_ids],
                                {'fields': ['name', 'date_order', 'amount_total']})
print("-----sales orders----", sale_orders)
# Print out the details of each sale order
for order in sale_orders:
    print("Order Name:", order['name'])
    print("Date:", order['date_order'])
    print("Total Amount:", order['amount_total'])
    print("------------------------")
