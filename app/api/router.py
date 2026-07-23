from fastapi import APIRouter

from app.api.routes import admin, auth, bookings, catalog, health, payments

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(catalog.router)
api_router.include_router(admin.router)
api_router.include_router(bookings.router)
api_router.include_router(payments.router)
