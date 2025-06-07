"""
프로젝트 설정 관리
"""

import os
from typing import Optional
from pydantic import BaseSettings


class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # 애플리케이션 기본 설정
    app_name: str = "Celery 이커머스 주문 처리 시스템"
    debug: bool = True
    api_version: str = "v1"
    
    # Redis 설정 (Celery Broker & Result Backend)
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    
    # Celery 설정
    celery_broker_url: str = f"redis://{redis_host}:{redis_port}/{redis_db}"
    celery_result_backend: str = f"redis://{redis_host}:{redis_port}/{redis_db}"
    
    # 이메일 설정 (예제용 - 실제 환경에서는 환경변수로 설정)
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    email_user: str = "your-email@gmail.com"
    email_password: str = "your-app-password"
    
    # 파일 저장 경로
    invoice_dir: str = "invoices"
    temp_dir: str = "temp"
    log_dir: str = "logs"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# 설정 인스턴스
settings = Settings() 