from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, customers, products, enquiries, services, sales, notifications, regions, reports, dispatch, password_reset

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(customers.router, prefix="/customers", tags=["customers"])
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(enquiries.router, prefix="/enquiries", tags=["enquiries"])
api_router.include_router(services.router, prefix="/services", tags=["services"])
api_router.include_router(sales.router, prefix="/sales", tags=["sales"])
api_router.include_router(dispatch.router, prefix="/dispatch", tags=["dispatch"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(regions.router, prefix="/regions", tags=["regions"])
api_router.include_router(password_reset.router, prefix="/password-reset", tags=["password-reset"])