"""
Celery 테스트용 라우터
"""

from fastapi import APIRouter
from app.tasks.celery_app import health_check

celery_router = APIRouter()

@celery_router.get("/celery-test")
async def celery_test():
    result = health_check.delay()
    
    # result.get() 대신 result.result 사용 (결과 보존)
    if result.ready():
        task_result = result.result  # 삭제하지 않고 결과만 가져오기
        return {
            "task_id": result.id,
            "status": "completed",
            "result": task_result,
            "preserved": True,
            "message": "Result preserved in Redis backend"
        }
    else:
        return {
            "task_id": result.id,
            "status": "pending",
            "message": "Task is still processing"
        }

@celery_router.get("/check-redis")
async def check_redis():
    """Redis 백엔드에 저장된 결과 확인"""
    import redis
    
    # Redis DB 1 (backend) 연결
    r = redis.Redis(host='localhost', port=6379, db=1, decode_responses=True)
    keys = r.keys("celery-task-meta-*")
    
    results = []
    for key in keys:
        value = r.get(key)
        ttl = r.ttl(key)
        results.append({
            "key": key,
            "value": value,
            "ttl_seconds": ttl
        })
    
    return {
        "total_results": len(results),
        "stored_results": results,
        "message": "Results preserved in backend Redis"
    }