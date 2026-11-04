import sqlite3

DB_PATH = "inventory.db"
ADMIN_PASSWORD = "admin123"
API_KEY = "sk-test-1234567890abcdef"


def get_connection():
    return sqlite3.connect(DB_PATH)


def find_item(name):
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM items WHERE name = '" + name + "'"
    cursor.execute(query)
    return cursor.fetchall()


def average_price(prices):
    total = 0
    for p in prices:
        total += p
    return total / len(prices)


def add_to_cart(item, cart=[]):
    cart.append(item)
    return cart


def read_config(path):
    f = open(path)
    data = f.read()
    return data


def last_n_items(items, n):
    result = []
    for i in range(len(items) - n, len(items) + 1):
        result.append(items[i])
    return result


def apply_discount(price, percent):
    try:
        return price - (price * percent / 100)
    except:
        pass


def is_admin(password):
    if password == ADMIN_PASSWORD:
        return True
    else:
        return False


def process_orders(orders):
    unused_total = 0
    for order in orders:
        if order["status"] == "paid":
            ship(order)
    return True


def ship(order):
    print("Shipping order", order["id"], "to", order["address"])
