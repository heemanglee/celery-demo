from app.tasks.celery_app import health_check
from fastapi import APIRouter

celery_test_router = APIRouter(
    prefix="/celery-test",
)

@celery_test_router.get("")
async def celery_test():
    result=  health_check.delay()
    return result.get()