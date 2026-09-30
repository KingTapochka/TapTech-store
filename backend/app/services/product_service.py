from app.database import get_db_connection, release_db_connection

def get_all_products():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, price, image_url FROM products ORDER BY id"
            )
            rows = cur.fetchall()
            return [
                {"id": r[0], "name": r[1], "price": r[2], "image_url": r[3]}
                for r in rows
            ]
    finally:
        release_db_connection(conn)

def get_product_by_id(product_id: int):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, price, image_url FROM products WHERE id = %s",
                (product_id,)
            )
            row = cur.fetchone()
            if row:
                return {"id": row[0], "name": row[1], "price": row[2], "image_url": row[3]}
            return None
    finally:
        release_db_connection(conn)

def get_products_by_ids(product_ids: list):
    if not product_ids:
        return []
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, price FROM products WHERE id = ANY(%s)",
                (product_ids,)
            )
            rows = cur.fetchall()
            return [{"id": r[0], "name": r[1], "price": r[2]} for r in rows]
    finally:
        release_db_connection(conn)
