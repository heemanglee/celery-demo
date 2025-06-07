"""
FastAPI 애플리케이션 메인 진입점
"""

from fastapi import FastAPI
from app.core.config import settings


def create_app() -> FastAPI:
    """FastAPI 애플리케이션 팩토리"""
    
    app = FastAPI(
        title=settings.app_name,
        version=settings.api_version,
        debug=settings.debug,
        description="Celery를 활용한 이커머스 주문 처리 시스템",
    )
    
    # 라우터 등록 (추후 구현)
    # app.include_router(orders.router, prefix="/api/v1/orders", tags=["orders"])
    
    @app.get("/")
    async def root():
        return {
            "message": f"Welcome to {settings.app_name}",
            "version": settings.api_version,
            "docs": "/docs"
        }
    
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "redis": "connected"}
    
    return app


# 애플리케이션 인스턴스
app = create_app() 