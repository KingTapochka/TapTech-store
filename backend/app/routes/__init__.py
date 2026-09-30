from fastapi import APIRouter
from .products import router as products_router
from .cart import router as cart_router
from .orders import router as orders_router
from .health import router as health_router

api_router = APIRouter(prefix="/api")
api_router.include_router(products_router)
api_router.include_router(cart_router)
api_router.include_router(orders_router)
api_router.include_router(health_router)
