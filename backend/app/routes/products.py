from fastapi import APIRouter, HTTPException
from app.models import ProductResponse
from app.services import get_all_products, get_product_by_id

router = APIRouter(prefix="/products", tags=["products"])

@router.get("/", response_model=list[ProductResponse])
def list_products():
    return get_all_products()

@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int):
    product = get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product
