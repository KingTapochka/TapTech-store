from fastapi import APIRouter, Request, HTTPException
import json
import uuid
from app.database import redis_client
from app.models import OrderCreate, OrderResponse
from app.services import get_products_by_ids, create_order

router = APIRouter(prefix="/orders", tags=["orders"])

def get_session_id(request: Request) -> str:
    session_id = request.headers.get("X-Session-Id")
    if not session_id:
        session_id = str(uuid.uuid4())
    return session_id

@router.post("/", response_model=OrderResponse)
def place_order(request: Request, order_data: OrderCreate):
    session_id = get_session_id(request)
    cart_key = f"cart:{session_id}"
    cart_json = redis_client.get(cart_key)
    if not cart_json:
        raise HTTPException(status_code=400, detail="Cart is empty")
    
    cart = json.loads(cart_json)
    if not cart:
        raise HTTPException(status_code=400, detail="Cart is empty")

    product_ids = [item["product_id"] for item in cart]
    products = get_products_by_ids(product_ids)
    product_map = {p["id"]: p for p in products}

    # Проверяем, что все товары есть
    missing = [pid for pid in product_ids if pid not in product_map]
    if missing:
        raise HTTPException(status_code=400, detail=f"Products not found: {missing}")

    order_items = []
    total = 0
    for item in cart:
        pid = item["product_id"]
        qty = item["quantity"]
        p = product_map[pid]
        order_items.append({
            "product_id": pid,
            "name": p["name"],
            "price": p["price"],
            "quantity": qty
        })
        total += p["price"] * qty

    customer_info = {
        "name": order_data.customer_name,
        "phone": order_data.customer_phone,
        "address": order_data.customer_address
    }
    order_id = create_order(session_id, order_items, customer_info, total)

    # Очищаем корзину
    redis_client.delete(cart_key)

    return OrderResponse(order_id=order_id, status="new", total_price=total)
