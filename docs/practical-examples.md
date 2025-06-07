# 이커머스 주문 처리 시스템 실습 가이드

## 🛠️ 프로젝트 구조

```
celery-demo/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 애플리케이션
│   ├── celery_app.py        # Celery 설정
│   ├── tasks/
│   │   ├── __init__.py
│   │   ├── email_tasks.py   # 이메일 관련 작업
│   │   ├── invoice_tasks.py # 인보이스 관련 작업
│   │   └── shipping_tasks.py # 배송 관련 작업
│   ├── models/
│   │   ├── __init__.py
│   │   └── order.py         # 주문 모델
│   └── config.py            # 설정
├── invoices/                # 생성된 인보이스 저장
├── requirements.txt
└── README.md
```

## 📦 1단계: 의존성 설치

### requirements.txt
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
celery[redis]==5.3.4
redis==5.0.1
pydantic==2.5.0
reportlab==4.0.7
python-multipart==0.0.6
python-decouple==3.8
flower==2.0.1
```

### 설치 명령
```bash
pip install -r requirements.txt
```

## ⚙️ 2단계: 기본 설정

### app/config.py
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Redis 설정
    redis_url: str = "redis://localhost:6379/0"
    
    # Celery 설정
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
    
    # 이메일 설정 (실습용 - 실제로는 SMTP 서버 사용)
    email_enabled: bool = True
    
    # 파일 경로
    invoice_dir: str = "invoices"
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### app/celery_app.py
```python
from celery import Celery
from app.config import settings

# Celery 애플리케이션 인스턴스 생성
celery_app = Celery(
    "ecommerce_tasks",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.tasks.email_tasks",
        "app.tasks.invoice_tasks", 
        "app.tasks.shipping_tasks"
    ]
)

# Celery 설정
celery_app.conf.update(
    # 작업 직렬화 형식
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    
    # 시간대 설정
    timezone="Asia/Seoul",
    enable_utc=True,
    
    # 작업 라우팅
    task_routes={
        "app.tasks.email_tasks.*": {"queue": "email"},
        "app.tasks.invoice_tasks.*": {"queue": "invoice"},
        "app.tasks.shipping_tasks.*": {"queue": "shipping"},
    },
    
    # 재시도 설정
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)
```

## 📊 3단계: 데이터 모델

### app/models/order.py
```python
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime
from enum import Enum

class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class OrderItem(BaseModel):
    product_id: int
    product_name: str
    quantity: int
    unit_price: float
    total_price: float

class ShippingAddress(BaseModel):
    name: str
    street: str
    city: str
    postal_code: str
    country: str
    phone: str

class OrderCreate(BaseModel):
    customer_email: EmailStr
    customer_name: str
    items: List[OrderItem]
    shipping_address: ShippingAddress
    total_amount: float

class Order(OrderCreate):
    id: int
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class OrderResponse(BaseModel):
    order_id: int
    status: str
    message: str
    task_ids: dict  # 백그라운드 작업 ID들
```

## 📧 4단계: 이메일 작업 구현

### app/tasks/email_tasks.py
```python
import time
import logging
from celery import current_task
from app.celery_app import celery_app
from app.models.order import Order

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
def send_order_confirmation_email(self, order_data: dict):
    """주문 확인 이메일 발송"""
    try:
        # 진행률 업데이트
        self.update_state(state='PROGRESS', meta={'progress': 0, 'status': '이메일 준비 중...'})
        
        order = Order(**order_data)
        
        # 이메일 내용 생성
        self.update_state(state='PROGRESS', meta={'progress': 30, 'status': '이메일 내용 생성 중...'})
        email_content = f"""
        안녕하세요 {order.customer_name}님,
        
        주문이 성공적으로 접수되었습니다.
        
        주문 번호: {order.id}
        주문 금액: {order.total_amount:,.0f}원
        
        주문 내역:
        """
        
        for item in order.items:
            email_content += f"- {item.product_name} x {item.quantity}개: {item.total_price:,.0f}원\n"
        
        # 이메일 발송 시뮬레이션 (실제로는 SMTP 서버 사용)
        self.update_state(state='PROGRESS', meta={'progress': 70, 'status': '이메일 발송 중...'})
        time.sleep(2)  # 이메일 발송 시간 시뮬레이션
        
        self.update_state(state='PROGRESS', meta={'progress': 100, 'status': '이메일 발송 완료'})
        
        logger.info(f"주문 {order.id} 확인 이메일이 {order.customer_email}로 발송되었습니다")
        
        return {
            "status": "success",
            "message": f"주문 확인 이메일이 {order.customer_email}로 발송되었습니다",
            "order_id": order.id
        }
        
    except Exception as e:
        logger.error(f"이메일 발송 실패 - 주문 {order_data.get('id')}: {e}")
        # 재시도 횟수 확인
        if self.request.retries < self.max_retries:
            logger.info(f"이메일 발송 재시도 {self.request.retries + 1}/{self.max_retries}")
            raise self.retry(countdown=60)
        else:
            return {
                "status": "failed",
                "message": f"이메일 발송 실패: {str(e)}",
                "order_id": order_data.get('id')
            }

@celery_app.task
def send_shipping_notification(order_id: int, tracking_number: str):
    """배송 시작 알림 이메일"""
    try:
        time.sleep(1)  # 이메일 발송 시뮬레이션
        
        logger.info(f"주문 {order_id} 배송 시작 알림 발송완료 (운송장: {tracking_number})")
        
        return {
            "status": "success",
            "message": f"배송 시작 알림이 발송되었습니다",
            "order_id": order_id,
            "tracking_number": tracking_number
        }
    except Exception as e:
        logger.error(f"배송 알림 발송 실패 - 주문 {order_id}: {e}")
        return {"status": "failed", "message": str(e)}
```

## 📄 5단계: PDF 인보이스 생성

### app/tasks/invoice_tasks.py
```python
import os
import time
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from app.celery_app import celery_app
from app.models.order import Order
from app.config import settings

@celery_app.task(bind=True)
def generate_invoice_pdf(self, order_data: dict):
    """PDF 인보이스 생성"""
    try:
        # 진행률 업데이트
        self.update_state(state='PROGRESS', meta={'progress': 0, 'status': 'PDF 생성 준비 중...'})
        
        order = Order(**order_data)
        
        # 인보이스 디렉토리 생성
        os.makedirs(settings.invoice_dir, exist_ok=True)
        
        # 파일명 생성
        filename = f"invoice_{order.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(settings.invoice_dir, filename)
        
        self.update_state(state='PROGRESS', meta={'progress': 20, 'status': 'PDF 문서 구성 중...'})
        
        # PDF 문서 생성
        doc = SimpleDocTemplate(filepath, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # 제목
        title = Paragraph("주문 인보이스", styles['Title'])
        story.append(title)
        story.append(Spacer(1, 12))
        
        # 주문 정보
        order_info = [
            ["주문 번호:", str(order.id)],
            ["고객명:", order.customer_name],
            ["이메일:", order.customer_email],
            ["주문일:", order.created_at.strftime("%Y-%m-%d %H:%M:%S")],
        ]
        
        order_table = Table(order_info)
        order_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.grey),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        
        story.append(order_table)
        story.append(Spacer(1, 12))
        
        self.update_state(state='PROGRESS', meta={'progress': 50, 'status': '주문 항목 추가 중...'})
        
        # 주문 항목 테이블
        items_data = [["상품명", "수량", "단가", "합계"]]
        for item in order.items:
            items_data.append([
                item.product_name,
                str(item.quantity),
                f"{item.unit_price:,.0f}원",
                f"{item.total_price:,.0f}원"
            ])
        
        items_data.append(["", "", "총합계", f"{order.total_amount:,.0f}원"])
        
        items_table = Table(items_data)
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (-2, -1), (-1, -1), colors.beige),
            ('FONTNAME', (-2, -1), (-1, -1), 'Helvetica-Bold'),
        ]))
        
        story.append(items_table)
        
        self.update_state(state='PROGRESS', meta={'progress': 80, 'status': 'PDF 파일 저장 중...'})
        
        # PDF 생성
        doc.build(story)
        
        # 생성 시간 시뮬레이션
        time.sleep(1)
        
        self.update_state(state='PROGRESS', meta={'progress': 100, 'status': 'PDF 생성 완료'})
        
        return {
            "status": "success",
            "message": "PDF 인보이스가 생성되었습니다",
            "order_id": order.id,
            "filename": filename,
            "filepath": filepath
        }
        
    except Exception as e:
        return {
            "status": "failed",
            "message": f"PDF 생성 실패: {str(e)}",
            "order_id": order_data.get('id')
        }
```

## 🚚 6단계: 배송 시스템 연동

### app/tasks/shipping_tasks.py
```python
import time
import random
import logging
from app.celery_app import celery_app
from app.models.order import Order, ShippingAddress

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 2, 'countdown': 30})
def register_shipping_info(self, order_data: dict):
    """배송 파트너사에 배송 정보 등록"""
    try:
        self.update_state(state='PROGRESS', meta={'progress': 0, 'status': '배송 시스템 연결 중...'})
        
        order = Order(**order_data)
        shipping_address = order.shipping_address
        
        # 외부 API 호출 시뮬레이션
        self.update_state(state='PROGRESS', meta={'progress': 30, 'status': '배송 정보 전송 중...'})
        
        # API 호출 시뮬레이션 (때때로 실패)
        if random.random() < 0.2:  # 20% 확률로 실패
            raise Exception("배송 시스템 일시적 오류")
        
        time.sleep(2)  # API 응답 대기 시뮬레이션
        
        # 운송장 번호 생성
        tracking_number = f"TRK{order.id}{random.randint(1000, 9999)}"
        
        self.update_state(state='PROGRESS', meta={'progress': 70, 'status': '운송장 번호 생성 중...'})
        
        # 배송 정보 등록 완료
        shipping_info = {
            "order_id": order.id,
            "tracking_number": tracking_number,
            "recipient": shipping_address.name,
            "address": f"{shipping_address.street}, {shipping_address.city}",
            "phone": shipping_address.phone,
            "estimated_delivery": "2-3일 후"
        }
        
        self.update_state(state='PROGRESS', meta={'progress': 100, 'status': '배송 등록 완료'})
        
        logger.info(f"주문 {order.id} 배송 정보 등록 완료 - 운송장: {tracking_number}")
        
        # 배송 시작 알림 이메일 발송 (체인 작업)
        from app.tasks.email_tasks import send_shipping_notification
        send_shipping_notification.delay(order.id, tracking_number)
        
        return {
            "status": "success",
            "message": "배송 정보가 등록되었습니다",
            "shipping_info": shipping_info
        }
        
    except Exception as e:
        logger.error(f"배송 정보 등록 실패 - 주문 {order_data.get('id')}: {e}")
        
        if self.request.retries < self.max_retries:
            logger.info(f"배송 등록 재시도 {self.request.retries + 1}/{self.max_retries}")
            raise self.retry(countdown=30)
        else:
            return {
                "status": "failed",
                "message": f"배송 정보 등록 실패: {str(e)}",
                "order_id": order_data.get('id')
            }

@celery_app.task
def update_shipping_status(order_id: int, status: str):
    """배송 상태 업데이트"""
    try:
        time.sleep(1)  # 상태 업데이트 시뮬레이션
        
        logger.info(f"주문 {order_id} 배송 상태 업데이트: {status}")
        
        return {
            "status": "success",
            "message": f"배송 상태가 '{status}'로 업데이트되었습니다",
            "order_id": order_id,
            "new_status": status
        }
    except Exception as e:
        logger.error(f"배송 상태 업데이트 실패 - 주문 {order_id}: {e}")
        return {"status": "failed", "message": str(e)}
```

## 🌐 7단계: FastAPI 웹 애플리케이션

### app/main.py
```python
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from app.models.order import OrderCreate, OrderResponse, Order
from app.tasks.email_tasks import send_order_confirmation_email
from app.tasks.invoice_tasks import generate_invoice_pdf
from app.tasks.shipping_tasks import register_shipping_info
from app.celery_app import celery_app
from datetime import datetime
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="이커머스 주문 처리 시스템",
    description="Celery를 활용한 비동기 주문 처리 시스템",
    version="1.0.0"
)

# 임시 주문 저장소 (실제로는 데이터베이스 사용)
orders_db = {}
order_counter = 1

@app.post("/orders", response_model=OrderResponse)
async def create_order(order_data: OrderCreate):
    """주문 생성 및 백그라운드 작업 시작"""
    global order_counter
    
    try:
        # 주문 생성
        order = Order(
            id=order_counter,
            **order_data.dict(),
            created_at=datetime.now()
        )
        
        # 임시 저장
        orders_db[order_counter] = order
        order_counter += 1
        
        # 백그라운드 작업들을 비동기로 시작
        order_dict = order.dict()
        
        # 1. 주문 확인 이메일 발송
        email_task = send_order_confirmation_email.delay(order_dict)
        
        # 2. PDF 인보이스 생성  
        invoice_task = generate_invoice_pdf.delay(order_dict)
        
        # 3. 배송 정보 등록
        shipping_task = register_shipping_info.delay(order_dict)
        
        logger.info(f"주문 {order.id} 생성 완료 - 백그라운드 작업 시작됨")
        
        return OrderResponse(
            order_id=order.id,
            status="confirmed",
            message="주문이 성공적으로 접수되었습니다. 확인 이메일과 인보이스가 곧 발송됩니다.",
            task_ids={
                "email_task": email_task.id,
                "invoice_task": invoice_task.id,
                "shipping_task": shipping_task.id
            }
        )
        
    except Exception as e:
        logger.error(f"주문 생성 실패: {e}")
        raise HTTPException(status_code=500, detail=f"주문 처리 중 오류가 발생했습니다: {str(e)}")

@app.get("/orders/{order_id}")
async def get_order(order_id: int):
    """주문 정보 조회"""
    if order_id not in orders_db:
        raise HTTPException(status_code=404, detail="주문을 찾을 수 없습니다")
    
    return orders_db[order_id]

@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """작업 상태 조회"""
    try:
        result = celery_app.AsyncResult(task_id)
        
        if result.state == 'PENDING':
            response = {
                "state": result.state,
                "status": "작업이 아직 시작되지 않았습니다"
            }
        elif result.state == 'PROGRESS':
            response = {
                "state": result.state,
                "progress": result.info.get('progress', 0),
                "status": result.info.get('status', '')
            }
        elif result.state == 'SUCCESS':
            response = {
                "state": result.state,
                "result": result.result
            }
        else:  # FAILURE
            response = {
                "state": result.state,
                "error": str(result.info)
            }
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"작업 상태 조회 실패: {str(e)}")

@app.get("/")
async def root():
    """API 루트 엔드포인트"""
    return {
        "message": "이커머스 주문 처리 시스템",
        "description": "Celery를 활용한 비동기 작업 처리",
        "endpoints": {
            "POST /orders": "새 주문 생성",
            "GET /orders/{order_id}": "주문 정보 조회",
            "GET /tasks/{task_id}": "작업 상태 조회"
        }
    }

# 애플리케이션 시작 시 실행
@app.on_event("startup")
async def startup_event():
    logger.info("이커머스 주문 처리 시스템이 시작되었습니다")

# 애플리케이션 종료 시 실행
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("이커머스 주문 처리 시스템이 종료되었습니다")
```

## 🚀 8단계: 실행 가이드

### Redis 서버 시작
```bash
# macOS (Homebrew)
brew services start redis

# 또는 직접 실행
redis-server
```

### Celery Worker 시작
```bash
# 기본 워커 시작
celery -A app.celery_app worker --loglevel=info

# 특정 큐만 처리하는 워커
celery -A app.celery_app worker --loglevel=info --queues=email
celery -A app.celery_app worker --loglevel=info --queues=invoice  
celery -A app.celery_app worker --loglevel=info --queues=shipping
```

### FastAPI 애플리케이션 시작
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Flower 모니터링 시작
```bash
celery -A app.celery_app flower --port=5555
```

## 🧪 9단계: 테스트

### API 테스트 (curl)
```bash
# 주문 생성
curl -X POST "http://localhost:8000/orders" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_email": "customer@example.com",
    "customer_name": "홍길동",
    "items": [
      {
        "product_id": 1,
        "product_name": "노트북",
        "quantity": 1,
        "unit_price": 1500000,
        "total_price": 1500000
      }
    ],
    "shipping_address": {
      "name": "홍길동",
      "street": "서울시 강남구 테헤란로 123",
      "city": "서울",
      "postal_code": "12345",
      "country": "대한민국",
      "phone": "010-1234-5678"
    },
    "total_amount": 1500000
  }'

# 작업 상태 확인
curl "http://localhost:8000/tasks/{task_id}"
```

### Python 클라이언트 테스트
```python
import requests
import time

# 주문 생성
order_data = {
    "customer_email": "test@example.com",
    "customer_name": "테스트 고객",
    "items": [
        {
            "product_id": 1,
            "product_name": "상품1",
            "quantity": 2,
            "unit_price": 50000,
            "total_price": 100000
        }
    ],
    "shipping_address": {
        "name": "테스트 고객",
        "street": "테스트 주소",
        "city": "테스트 시",
        "postal_code": "12345",
        "country": "대한민국",
        "phone": "010-0000-0000"
    },
    "total_amount": 100000
}

response = requests.post("http://localhost:8000/orders", json=order_data)
result = response.json()

print(f"주문 생성: {result}")

# 작업 상태 추적
for task_type, task_id in result['task_ids'].items():
    print(f"\n{task_type} 상태 추적:")
    
    while True:
        status_response = requests.get(f"http://localhost:8000/tasks/{task_id}")
        status = status_response.json()
        
        print(f"  상태: {status}")
        
        if status['state'] in ['SUCCESS', 'FAILURE']:
            break
            
        time.sleep(2)
```

## 📊 10단계: 모니터링

### Flower 웹 인터페이스
- URL: http://localhost:5555
- 실시간 작업 상태 확인
- Worker 성능 모니터링
- 작업 히스토리 조회

### Redis 상태 확인
```bash
redis-cli info
redis-cli monitor
```

### 작업 큐 상태 확인
```bash
celery -A app.celery_app inspect active
celery -A app.celery_app inspect scheduled
celery -A app.celery_app inspect reserved
```

이 실습 가이드를 통해 실제 이커머스 시스템에서 사용되는 Celery 기반 비동기 처리 시스템을 완전히 구현하고 이해할 수 있습니다. 