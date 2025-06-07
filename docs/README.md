# 🛒 Celery 이커머스 주문 처리 시스템 학습 가이드

## 📚 문서 구성

이 저장소는 실제 이커머스 주문 처리 시나리오를 통해 Celery의 핵심 개념을 학습할 수 있도록 구성되어 있습니다.

### 📖 학습 문서 목록

1. **[celery-ecommerce-guide.md](./celery-ecommerce-guide.md)** - 메인 학습 가이드
   - Celery 기본 개념 설명
   - Producer, Broker, Worker 역할
   - 체크박스 기반 학습 목차
   - 핵심 학습 포인트

2. **[worker-process-guide.md](./worker-process-guide.md)** - Worker 심화 가이드
   - Worker가 Queue에서 Task를 처리하는 상세 과정
   - 실제 동작 시뮬레이션
   - Worker 내부 구조 분석
   - 오류 처리 및 복구 전략

3. **[practical-examples.md](./practical-examples.md)** - 실습 가이드
   - 완전한 코드 예제
   - 단계별 구현 가이드
   - 테스트 방법
   - 모니터링 도구 사용법

## 🎯 학습 목표

### 기본 목표
- [ ] Celery의 기본 아키텍처 이해
- [ ] Producer-Broker-Worker 패턴 이해
- [ ] 비동기 작업 처리의 필요성 이해

### 실무 목표
- [ ] 실제 이커머스 시스템에서의 Celery 활용
- [ ] Task 설계 및 구현 능력
- [ ] 오류 처리 및 재시도 전략 수립
- [ ] 모니터링 및 디버깅 역량

### 고급 목표
- [ ] 프로덕션 환경 배포 준비
- [ ] 성능 최적화 방법 이해
- [ ] 확장성 있는 시스템 설계

## 🚀 빠른 시작

### 1. 필수 요구사항
```bash
# Python 3.8 이상
python --version

# Redis 설치 및 실행
brew install redis
brew services start redis
```

### 2. 프로젝트 설정
```bash
# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 3. 시스템 실행
```bash
# Terminal 1: Redis 실행
redis-server

# Terminal 2: Celery Worker 실행
celery -A app.celery_app worker --loglevel=info

# Terminal 3: FastAPI 서버 실행
uvicorn app.main:app --reload

# Terminal 4: Flower 모니터링 (선택사항)
celery -A app.celery_app flower
```

## 📋 학습 체크리스트

### 🔰 초급 단계
- [ ] 1. [메인 가이드](./celery-ecommerce-guide.md) 읽기
- [ ] 2. Celery 기본 개념 이해
- [ ] 3. 시스템 구성 요소 역할 파악
- [ ] 4. 개발 환경 설정

### 🔧 중급 단계
- [ ] 5. [Worker 과정 가이드](./worker-process-guide.md) 학습
- [ ] 6. [실습 가이드](./practical-examples.md)의 1-4단계 완료
- [ ] 7. 기본 Task 구현 및 테스트
- [ ] 8. FastAPI 연동 완료

### 🚀 고급 단계
- [ ] 9. Task 체이닝 및 그룹 구현
- [ ] 10. 오류 처리 및 재시도 로직 구현
- [ ] 11. 모니터링 도구 활용
- [ ] 12. 성능 최적화 적용

## 🛠️ 실습 시나리오

### 주문 처리 워크플로우
```
고객 주문 → FastAPI 엔드포인트 → 즉시 응답
                ↓
         3개 백그라운드 Task 시작:
         ├── 📧 이메일 발송
         ├── 📄 PDF 인보이스 생성
         └── 🚚 배송 시스템 연동
```

### 처리되는 비동기 작업들
1. **이메일 발송 Task**
   - 주문 확인 이메일
   - 배송 시작 알림
   - 진행률 업데이트 포함

2. **PDF 인보이스 생성 Task**
   - ReportLab을 사용한 PDF 생성
   - 주문 정보 및 항목 포함
   - 파일 시스템에 저장

3. **배송 시스템 연동 Task**
   - 외부 API 호출 시뮬레이션
   - 운송장 번호 생성
   - 재시도 로직 포함

## 📊 모니터링 도구

### Flower 대시보드
- **URL**: http://localhost:5555
- **기능**: 실시간 작업 모니터링, Worker 상태 확인

### Redis 모니터링
```bash
# Redis 상태 확인
redis-cli info

# 실시간 명령어 모니터링
redis-cli monitor
```

### Celery 내장 도구
```bash
# 활성 작업 확인
celery -A app.celery_app inspect active

# Worker 통계
celery -A app.celery_app inspect stats
```

## 🚨 문제 해결

### 자주 발생하는 문제들

1. **Redis 연결 오류**
   ```bash
   # Redis 서버 상태 확인
   brew services list | grep redis
   
   # Redis 재시작
   brew services restart redis
   ```

2. **Celery Worker 시작 오류**
   ```bash
   # 모듈 경로 확인
   python -c "import app.celery_app"
   
   # 로그 레벨 상승으로 디버깅
   celery -A app.celery_app worker --loglevel=debug
   ```

3. **Task 등록 문제**
   ```bash
   # 등록된 Task 확인
   celery -A app.celery_app inspect registered
   ```

## 🎓 학습 완료 후

### 다음 단계 학습 권장사항
- [ ] Celery Beat을 활용한 스케줄링
- [ ] 다중 큐 및 라우팅 고급 설정
- [ ] Docker를 활용한 컨테이너화
- [ ] Kubernetes 환경에서의 Celery 배포
- [ ] 메시지 브로커 선택 (Redis vs RabbitMQ)

### 실무 적용 가이드
- [ ] 프로덕션 환경 보안 설정
- [ ] 로그 수집 및 분석 시스템 구축
- [ ] 알림 및 경고 시스템 구현
- [ ] 성능 벤치마킹 및 튜닝

## 📞 지원

### 학습 중 도움이 필요한 경우
1. 각 문서의 예제 코드를 단계별로 실행
2. 로그 메시지를 통한 문제 진단
3. Flower 대시보드를 통한 시각적 모니터링
4. Redis CLI를 통한 큐 상태 확인

### 참고 자료
- [Celery 공식 문서](https://docs.celeryq.dev/)
- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [Redis 공식 문서](https://redis.io/documentation)

---

**"실제 서비스에서 사용되는 수준의 Celery 시스템을 구축하고 이해해보세요!"** 🚀 