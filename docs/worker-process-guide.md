# Celery Worker의 작업 처리 과정 심화 가이드

## 🔄 Worker가 Queue에서 Task를 처리하는 과정

### 1. 대기 상태 (Idle State)
```
Worker -> Broker: "새로운 작업이 있나요?"
Broker -> Worker: "아직 없습니다"
Worker: 대기 상태 유지 (polling interval)
```

### 2. 작업 발견 및 수신
```
Producer -> Broker: Task 전송 (주문 처리 완료)
Broker: Queue에 Task 저장
Worker -> Broker: "새로운 작업이 있나요?" (정기적 폴링)
Broker -> Worker: "예, 새로운 Task가 있습니다" + Task 데이터
```

### 3. 작업 실행 과정

#### 3.1 Task 메타데이터 파싱
```python
# Worker가 수신한 Task 정보
{
    "id": "task-uuid-1234",
    "task": "tasks.send_order_confirmation_email",
    "args": [order_id, customer_email],
    "kwargs": {"order_details": {...}},
    "retries": 0,
    "eta": null,
    "expires": null
}
```

#### 3.2 Task 함수 로드 및 실행
```python
# Worker 내부 처리
1. Task 이름으로 함수 찾기: tasks.send_order_confirmation_email
2. 인자 준비: args=[12345, "customer@example.com"], kwargs={...}
3. 함수 실행: send_order_confirmation_email(12345, "customer@example.com", ...)
4. 결과 또는 예외 캐치
```

### 4. 결과 처리

#### 4.1 성공 시
```python
# Task 실행 성공
result = "이메일이 성공적으로 발송되었습니다"
Worker -> Broker: 결과 저장 (Result Backend)
Worker -> Broker: Task 완료 ACK 신호
Worker: 다음 작업 대기 상태로 전환
```

#### 4.2 실패 시
```python
# Task 실행 실패
try:
    result = send_order_confirmation_email(...)
except SMTPException as e:
    # 재시도 가능한 오류
    if retries < max_retries:
        Worker -> Broker: Task 재시도 요청 (delay 후)
    else:
        Worker -> Broker: Task 완전 실패 기록
except Exception as e:
    # 재시도 불가능한 오류
    Worker -> Broker: Task 실패 기록
```

## 🔧 실제 동작 시뮬레이션

### 시나리오: 주문 완료 후 3개 Task 처리

#### 초기 상태
```
Queue: [ ]
Worker1: 대기 중
Worker2: 대기 중
```

#### Producer가 작업 생성
```python
# FastAPI 엔드포인트에서
order_id = create_order(order_data)

# 3개 Task를 Queue에 추가
send_email.delay(order_id, customer_email)
generate_invoice.delay(order_id)
notify_shipping.delay(order_id, shipping_address)
```

#### Queue 상태 변화
```
Queue: [
    Task1: send_email(12345, "user@example.com"),
    Task2: generate_invoice(12345),
    Task3: notify_shipping(12345, {...})
]
Worker1: 대기 중
Worker2: 대기 중
```

#### Worker들이 작업 가져오기
```
Worker1 -> Broker: 작업 요청
Broker -> Worker1: Task1 할당
Queue: [Task2, Task3]
Worker1: Task1 실행 중

Worker2 -> Broker: 작업 요청  
Broker -> Worker2: Task2 할당
Queue: [Task3]
Worker2: Task2 실행 중
```

#### 작업 완료 및 결과 처리
```
Worker1: Task1 완료 -> "이메일 발송 성공"
Worker1 -> Broker: 결과 저장 및 ACK
Worker1: 다음 작업 대기

Worker2: Task2 완료 -> "PDF 인보이스 생성 완료"
Worker2 -> Broker: 결과 저장 및 ACK
Worker2: 다음 작업 대기

Worker1 -> Broker: 작업 요청
Broker -> Worker1: Task3 할당
Queue: [ ]
Worker1: Task3 실행 중
```

## 📊 Worker 내부 구조

### Worker 프로세스 구성
```
Worker Process
├── Consumer Thread (메시지 수신)
├── Executor Pool (작업 실행)
│   ├── Thread Pool 또는
│   └── Process Pool
├── Result Handler (결과 처리)
└── Beat Scheduler (선택적)
```

### 메모리 관리
```python
# Worker가 Task를 처리할 때 메모리 사용
Before Task: Worker Memory = 50MB
During Task: Worker Memory = 50MB + Task Memory
After Task: Worker Memory = 50MB (가비지 컬렉션)

# 메모리 누수 방지
CELERYD_MAX_TASKS_PER_CHILD = 1000  # 1000개 작업 후 Worker 재시작
```

## ⚙️ Worker 설정 옵션

### 동시 실행 설정
```bash
# Thread 기반 (I/O 집약적 작업에 적합)
celery -A app worker --concurrency=4 --pool=threads

# Process 기반 (CPU 집약적 작업에 적합)  
celery -A app worker --concurrency=4 --pool=prefork

# 단일 스레드 (디버깅용)
celery -A app worker --concurrency=1
```

### 작업 우선순위 처리
```python
# 높은 우선순위 큐
celery -A app worker --queues=high_priority,normal_priority

# Task에 우선순위 설정
send_urgent_email.apply_async(args=[...], priority=9)
send_normal_email.apply_async(args=[...], priority=5)
```

## 🚨 오류 처리 및 복구

### 재시도 메커니즘
```python
@celery.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
def send_email(self, order_id, email):
    try:
        # 이메일 발송 로직
        send_mail(...)
        return "성공"
    except SMTPException as e:
        # 자동 재시도 (60초 후)
        raise self.retry(countdown=60)
    except Exception as e:
        # 재시도 불가능한 오류
        logger.error(f"이메일 발송 실패: {e}")
        raise
```

### Dead Letter Queue
```python
# 실패한 작업을 별도 큐로 이동
CELERY_TASK_ROUTES = {
    'tasks.send_email': {
        'queue': 'email_queue',
        'routing_key': 'email',
        'dead_letter_queue': 'failed_emails'
    }
}
```

## 📈 모니터링 및 디버깅

### Worker 상태 확인
```bash
# Worker 상태 확인
celery -A app inspect active

# Worker 통계
celery -A app inspect stats

# 등록된 Task 목록
celery -A app inspect registered
```

### 실시간 모니터링
```bash
# Flower를 통한 웹 모니터링
celery -A app flower

# 실시간 이벤트 모니터링
celery -A app events
```

이러한 과정을 통해 Celery Worker는 효율적이고 안정적으로 백그라운드 작업을 처리하며, 시스템의 응답성과 확장성을 크게 향상시킵니다. 