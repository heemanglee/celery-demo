"""
Celery 애플리케이션 인스턴스 및 설정
"""

from celery import Celery
from app.core.config import settings

# Celery 애플리케이션 인스턴스 생성
celery_app = Celery(
    "ecommerce_order_system",  # 애플리케이션 이름
    broker=settings.celery_broker_url,  # 메시지 브로커 URL (Redis)
    backend=settings.celery_result_backend,  # 결과 백엔드 URL (Redis)
)

# Celery 기본 설정
celery_app.conf.update(
    # Celery 작업이 완료되어 Backend에 저장된 결과의 TTL (Time To Live) 설정
    result_expires=86400,
    
    # 결과 조회 시 자동 삭제 방지
    result_expires_on_consume=False,
    
    # 시간대 설정
    timezone='Asia/Seoul',
    
    # 시간대 인식 설정
    enable_utc=True,
    
    # 작업 직렬화 형식
    task_serializer='json',
    
    # 결과 직렬화 형식  
    result_serializer='json',
    
    # 허용할 직렬화 형식 목록
    accept_content=['json'],
    
    # 결과 압축 활성화
    result_compression='gzip',
    
    # 작업 압축 활성화
    task_compression='gzip',
    
    # 작업 실행 후 결과 무시 여부 (기본값: False)
    task_ignore_result=False,
    
    # 작업 추적 활성화
    task_track_started=True,
    
    # 작업 재시도 기본 설정
    task_default_retry_delay=60,  # 재시도 간격 (초)
    task_max_retries=3,  # 최대 재시도 횟수
    
    # Worker 설정
    worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
    worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s',
    
    # 작업 라우팅 (큐별 작업 분배)
    task_routes={
        'app.tasks.email_tasks.*': {'queue': 'email'},
        'app.tasks.pdf_tasks.*': {'queue': 'pdf'},  
        'app.tasks.shipping_tasks.*': {'queue': 'shipping'},
        'app.tasks.order_tasks.*': {'queue': 'orders'},
    },
    
    # 작업 우선순위 설정 (0이 가장 낮음, 9가 가장 높음)
    task_default_priority=5,
    worker_disable_rate_limits=True,
    
    # Beat 스케줄러 설정 (추후 구현)
    beat_schedule={},
)

# 자동으로 작업 모듈 탐지 (추후 작업 모듈들이 생성되면 자동 로드)
celery_app.autodiscover_tasks([
    'app.tasks.email_tasks',
    'app.tasks.pdf_tasks', 
    'app.tasks.shipping_tasks',
    'app.tasks.order_tasks',
])


@celery_app.task(bind=True)
def debug_task(self):
    """디버그용 테스트 작업"""
    print(f'Request: {self.request!r}')
    return f'Hello from Celery! Task ID: {self.request.id}'


# Celery 애플리케이션 상태 확인 작업
@celery_app.task
def health_check():
    """Celery 상태 확인용 간단한 작업"""
    return {
        'status': 'healthy',
        'message': 'Celery is working properly!',
        'broker': settings.celery_broker_url,
        'backend': settings.celery_result_backend,
    } 