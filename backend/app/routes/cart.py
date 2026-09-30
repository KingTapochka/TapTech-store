from fastapi import APIRouter, Request, HTTPException
import json
import uuid
from app.database import redis_client
from app.models import CartItemAdd

router = APIRouter(prefix="/cart", tags=["cart"])

def get_session_id(request: Request) -> str:
    session_id = request.headers.get("X-Session-Id")
    if not session_id:
        # генерация нового, но клиент должен сам хранить и передавать
        session_id = str(uuid.uuid4())
    return session_id

@router.post("/")
def add_to_cart(request: Request, item: CartItemAdd):
    session_id = get_session_id(request)
    cart_key = f"cart:{session_id}"
    cart_json = redis_client.get(cart_key)
    cart = json.loads(cart_json) if cart_json else []

    found = False
    for entry in cart:
        if entry["product_id"] == item.product_id:
            entry["quantity"] += item.quantity
            found = True
            break
    if not found:
        cart.append({"product_id": item.product_id, "quantity": item.quantity})

    redis_client.setex(cart_key, 60*60*24*7, json.dumps(cart))
    return {"cart": cart}
