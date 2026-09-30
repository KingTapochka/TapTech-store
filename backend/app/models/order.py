from pydantic import BaseModel

class OrderCreate(BaseModel):
    customer_name: str
    customer_phone: str
    customer_address: str

class OrderResponse(BaseModel):
    order_id: int
    status: str
    total_price: float
