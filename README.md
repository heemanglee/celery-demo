# Celery 이커머스 주문 처리 시스템

Celery를 활용한 비동기 작업 처리를 학습하기 위한 이커머스 주문 시스템 예제입니다.

## 🎯 프로젝트 개요

실제 이커머스 환경에서 발생하는 주문 처리 과정을 시뮬레이션하며 다음과 같은 비동기 작업들을 학습합니다:

- **주문 확인 이메일 발송**: 고객에게 주문 내역 이메일 전송
- **PDF 인보이스 생성**: 주문 정보를 바탕으로 인보이스 PDF 생성
- **배송 정보 전송**: 외부 배송 파트너 API 연동

## 🏗️ 프로젝트 구조

```
celery-demo/
├── app/                        # 메인 애플리케이션
│   ├── __init__.py
│   ├── main.py                 # FastAPI 애플리케이션 진입점
│   ├── core/                   # 핵심 설정
│   │   ├── __init__.py
│   │   └── config.py          # 프로젝트 설정 관리
│   ├── models/                 # 데이터 모델 (Pydantic)
│   │   └── __init__.py
│   ├── routers/                # API 라우터
│   │   └── __init__.py
│   ├── tasks/                  # Celery 작업 정의
│   │   └── __init__.py
│   └── utils/                  # 유틸리티 함수
│       └── __init__.py
├── invoices/                   # 생성된 PDF 인보이스 저장
├── temp/                       # 임시 파일 저장
├── logs/                       # 로그 파일 저장
├── docs/                       # 프로젝트 문서
│   └── celery-ecommerce-guide.md
├── docker-compose.yml          # Redis 컨테이너 설정
├── requirements.txt            # Python 의존성
├── .gitignore                 # Git 무시 규칙
└── README.md                  # 프로젝트 설명서
```

## 🚀 빠른 시작

### 1. 저장소 클론

```bash
git clone <repository-url>
cd celery-demo
```

### 2. 가상환경 생성 및 활성화

```bash
# Python 가상환경 생성
python -m venv venv

# 가상환경 활성화 (macOS/Linux)
source venv/bin/activate

# 가상환경 활성화 (Windows)
venv\Scripts\activate
```

### 3. 의존성 설치

```bash
pip install -r requirements.txt
```

### 4. Redis 서버 실행 (Docker)

```bash
# Redis 컨테이너 실행
docker-compose up -d redis

# Redis 연결 확인
docker exec celery-redis redis-cli ping
# 출력: PONG
```

## 📊 현재 접속 가능한 서비스

- **Redis**: localhost:6379

## 🛠️ 주요 기술 스택

- **웹 프레임워크**: FastAPI (설정 예정)
- **비동기 작업 처리**: Celery 5.x (설정 예정)
- **메시지 브로커**: Redis 7.x (완료)
- **PDF 생성**: ReportLab (구현 예정)
- **API 문서화**: FastAPI 자동 생성 (구현 예정)
- **모니터링**: Flower (설정 예정)

## 📚 학습 가이드

상세한 학습 가이드는 [`docs/celery-ecommerce-guide.md`](docs/celery-ecommerce-guide.md)를 참고하세요.

## 🔧 개발 도구

### Redis 컨테이너 관리

```bash
# Redis 컨테이너 시작
docker-compose up -d redis

# Redis 컨테이너 중지
docker-compose down

# Redis 컨테이너 로그 확인
docker-compose logs redis

# Redis CLI 접속
docker exec -it celery-redis redis-cli
```

### 프로젝트 상태 확인

```bash
# Redis 연결 상태 확인
docker exec celery-redis redis-cli ping

# Redis 컨테이너 상태 확인
docker-compose ps
```