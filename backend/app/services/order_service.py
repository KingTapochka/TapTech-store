import json
from app.database import get_db_connection, release_db_connection

def create_order(session_id: str, order_items: list, customer_info: dict, total_price: int):
    """
    order_items: список словарей с ключами product_id, name, price, quantity
    customer_info: словарь с ключами name, phone, address
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            order_json = json.dumps(order_items)
            cur.execute(
                """INSERT INTO orders 
                   (session_id, order_data, total_price, customer_name, customer_phone, customer_address, status)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)
                   RETURNING id""",
                (session_id, order_json, total_price,
                 customer_info["name"], customer_info["phone"], customer_info["address"],
                 'new')
            )
            order_id = cur.fetchone()[0]
            conn.commit()
            return order_id
    finally:
        release_db_connection(conn)
