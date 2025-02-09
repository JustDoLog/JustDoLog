# JustDoLog

JustDoLog는 개발자들을 위한 심플하고 강력한 블로깅 플랫폼입니다. Markdown 지원과 코드 하이라이팅 기능을 통해 기술 문서 작성에 최적화되어 있으며, PostgreSQL의 전문 검색 기능을 활용한 강력한 검색 기능을 제공합니다.

## 목차
- [JustDoLog](#justdolog)
  - [목차](#목차)
  - [주요 기능](#주요-기능)
  - [기술 스택](#기술-스택)
  - [시작하기](#시작하기)
    - [사전 요구사항](#사전-요구사항)
    - [개발 환경 설정](#개발-환경-설정)
    - [개발 환경 유용한 명령어들](#개발-환경-유용한-명령어들)
    - [프로덕션 환경 설정](#프로덕션-환경-설정)
  - [환경 변수](#환경-변수)
  - [데이터베이스](#데이터베이스)
  - [파일 스토리지 (MinIO)](#파일-스토리지-minio)
    - [MinIO 설정](#minio-설정)
    - [버킷 설정](#버킷-설정)
  - [Docker 사용하기](#docker-사용하기)
    - [개발 환경](#개발-환경)
    - [프로덕션 환경](#프로덕션-환경)
  - [기여하기](#기여하기)
  - [라이선스](#라이선스)
  - [환경 설정](#환경-설정)
    - [TinyMCE 설정](#tinymce-설정)
    - [MinIO 설정 상세](#minio-설정-상세)
    - [환경별 주요 차이점](#환경별-주요-차이점)
    - [보안 주의사항](#보안-주의사항)

## 주요 기능
- 마크다운 기반의 블로그 포스팅
- 코드 신택스 하이라이팅
- 소셜 로그인 (Google, GitHub)
- 반응형 디자인
- SEO 최적화
- PostgreSQL 기반 전문 검색 (한글 검색 지원)

## 기술 스택
- **Backend**
  - Python 3.12
  - Django 5.1
  - django-allauth (소셜 로그인)
  - django-tinymce (텍스트 에디터)
- **Database**
  - PostgreSQL 15 (프로덕션)
  - SQLite (개발)
- **Storage**
  - MinIO (S3 호환 객체 스토리지)
- **Infrastructure**
  - Docker & Docker Compose
  - Nginx (프로덕션)
  - Gunicorn (프로덕션)

## 시작하기

### 사전 요구사항
- Docker Engine 24.0.0 이상
- Docker Compose v2.24.0 이상
- Git

### 개발 환경 설정
1. 저장소 클론
```bash
git clone https://github.com/yourusername/JustDoLog.git
cd JustDoLog
```

2. 환경 변수 설정
```bash
cp env.dev.example .env.dev
# .env.dev 파일을 적절히 수정하세요
```

3. 개발 서버 실행 (백그라운드)
```bash
docker-compose -f docker-compose.dev.yml up --build -d
```

4. 데이터베이스 마이그레이션
```bash
docker-compose -f docker-compose.dev.yml exec web python manage.py migrate
```

5. 관리자 계정 생성
```bash
docker-compose -f docker-compose.dev.yml exec web python manage.py createsuperuser
```

이제 http://localhost:8000 에서 개발 서버에 접속할 수 있습니다. 관리자 페이지는 http://localhost:8000/admin/ 에서 확인할 수 있습니다.

### 개발 환경 유용한 명령어들

#### Docker 관련 명령어
```bash
# 서버 시작
docker-compose -f docker-compose.dev.yml up --build -d

# 서버 로그 확인
docker-compose -f docker-compose.dev.yml logs -f

# 특정 컨테이너 로그만 확인
docker-compose -f docker-compose.dev.yml logs -f web

# Django 관리 명령어 실행
docker-compose -f docker-compose.dev.yml exec web python manage.py [command]

# 서버 재시작
docker-compose -f docker-compose.dev.yml restart

# 서버 중지
docker-compose -f docker-compose.dev.yml down

# 서버 중지 및 볼륨 삭제 (데이터베이스 초기화)
docker-compose -f docker-compose.dev.yml down -v

# 컨테이너, 이미지, 볼륨 모두 제거 (초기화)
docker-compose -f docker-compose.dev.yml down -v --rmi all
```

#### Django 관리 명령어
```bash
# 데이터베이스 마이그레이션
python manage.py makemigrations  # 모델 변경사항 마이그레이션 파일 생성
python manage.py migrate         # 마이그레이션 적용

# 테스트 데이터 생성
python manage.py generate_test_data  # 테스트용 데이터 생성
python manage.py generate_test_data --users 10 --posts 5  # 10명의 사용자, 각 5개의 포스트 생성

# 정적 파일 수집
python manage.py collectstatic  # 정적 파일 수집

# 개발 서버 실행
python manage.py runserver  # 기본 포트(8000)로 실행
python manage.py runserver 8080  # 특정 포트로 실행
python manage.py runserver 0.0.0.0:8000  # 모든 IP에서 접근 가능하도록 실행

# Django 쉘
python manage.py shell  # Django 쉘 실행 (일반)
python manage.py shell_plus  # Django 확장 쉘 실행 (django-extensions 필요)

# 데이터베이스 백업 및 복원
python manage.py dumpdata > db.json  # 전체 데이터 백업
python manage.py dumpdata blog > blog.json  # 특정 앱의 데이터만 백업
python manage.py loaddata db.json  # 데이터 복원

# 캐시 삭제
python manage.py clear_cache  # 캐시 삭제

# 테스트
python manage.py test  # 전체 테스트 실행
python manage.py test blog  # 특정 앱의 테스트만 실행
python manage.py test blog.tests.test_views  # 특정 테스트 파일만 실행
python manage.py test blog.tests.test_views -k test_create_post  # 특정 테스트 케이스만 실행
```

#### 코드 품질 관리
```bash
# 코드 포맷팅
black .  # 코드 스타일 자동 수정

# 코드 린팅
flake8 .  # 코드 품질 검사

# Import 문 정렬
isort .  # 파이썬 import 문 자동 정렬
```

### 프로덕션 환경 설정
1. 환경 변수 설정
```bash
cp env.example .env
# .env 파일을 프로덕션 환경에 맞게 수정하세요
```

2. 프로덕션 서버 실행
```bash
docker-compose -f docker-compose.prod.yml up --build -d
```

3. 데이터베이스 마이그레이션
```bash
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
```

4. 정적 파일 수집
```bash
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

## 환경 변수
프로젝트에서 사용되는 주요 환경 변수:

| 변수명 | 설명 | 기본값 | 필수 여부 |
|--------|------|---------|-----------|
| DJANGO_SETTINGS_MODULE | Django 설정 모듈 | config.settings.local | Yes |
| DJANGO_SECRET_KEY | Django 보안 키 | - | Yes |
| DEBUG | 디버그 모드 활성화 | True (개발) / False (프로덕션) | Yes |
| ALLOWED_HOSTS | 허용된 호스트 | localhost,127.0.0.1 | Yes |
| DB_NAME | 데이터베이스 이름 | justdolog | Yes |
| DB_USER | 데이터베이스 사용자 | justdolog_user | Yes |
| DB_PASSWORD | 데이터베이스 비밀번호 | - | Yes |
| DB_HOST | 데이터베이스 호스트 | db | Yes |
| DB_PORT | 데이터베이스 포트 | 5432 | Yes |
| MINIO_ROOT_USER | MinIO 접근 키 | admin | Yes |
| MINIO_ROOT_PASSWORD | MinIO 시크릿 키 | miniosecret | Yes |
| MINIO_BUCKET_NAME | MinIO 버킷 이름 | justdolog-media | Yes |
| MINIO_URL | MinIO 엔드포인트 URL | http://localhost:9000 | Yes |

## 데이터베이스
- 개발 환경: SQLite
- 프로덕션 환경: PostgreSQL 15
  - 한글 전문 검색을 위한 확장 기능 활성화
    - pg_trgm
    - unaccent
  - 자동 검색 벡터 업데이트를 위한 트리거 설정

## 파일 스토리지 (MinIO)
프로젝트는 이미지 및 파일 저장을 위해 MinIO를 사용합니다.

### MinIO 설정
1. MinIO 서버 실행 (개발 환경)
```bash
# docker-compose.dev.yml에 포함되어 있어 별도 실행 불필요
docker-compose -f docker-compose.dev.yml up -d
```

2. MinIO 서버 실행 (프로덕션 환경)
```bash
docker-compose -f docker-compose.prod.yml up -d
```

3. MinIO 콘솔 접속
- 개발 환경: http://localhost:9001
  - 기본 계정: admin / miniosecret
  - ⚠️ 보안을 위해 반드시 비밀번호를 변경하세요!
- 프로덕션 환경: https://your-domain:9001

### 버킷 설정
1. MinIO 콘솔에 접속 (http://localhost:9001)
2. 기본 계정으로 로그인 (admin / miniosecret)
3. 비밀번호 변경
   - 우측 상단 프로필 메뉴 → Change Password
   - 안전한 새 비밀번호로 변경
4. 버킷은 자동으로 생성됩니다
   - 기본 버킷 이름: justdolog-media
   - 기본 접근 정책: public

### 주의사항
- 개발 환경의 기본 자격 증명 (admin / miniosecret)은 절대 프로덕션에서 사용하지 마세요
- 프로덕션 환경에서는 반드시:
  1. 강력한 비밀번호를 사용
  2. HTTPS를 활성화
  3. 적절한 버킷 정책을 설정
  4. 정기적인 백업 구성

## Docker 사용하기

### 개발 환경
```bash
# 서버 시작
docker-compose up

# 백그라운드 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f

# Django 관리 명령어
docker-compose exec web python manage.py [command]

# 서버 중지
docker-compose down
```

### 프로덕션 환경
```bash
# 프로덕션 서버 시작
docker-compose -f docker-compose.prod.yml up -d

# 로그 확인
docker-compose -f docker-compose.prod.yml logs -f

# 서버 중지
docker-compose -f docker-compose.prod.yml down
```

## 기여하기
프로젝트에 기여하고 싶으시다면:
1. 이슈를 생성하거나 기존 이슈를 확인해주세요
2. 새로운 브랜치를 생성하세요 (`git checkout -b feature/amazing-feature`)
3. 변경사항을 커밋하세요 (`git commit -m 'feat: Add amazing feature'`)
4. 브랜치를 푸시하세요 (`git push origin feature/amazing-feature`)
5. Pull Request를 생성하세요

## 라이선스
이 프로젝트는 MIT 라이선스를 따릅니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참고하세요.

## 환경 설정

### TinyMCE 설정
- `SITE_URL`: 사이트 기본 URL (예: http://localhost:8000)
- TinyMCE 이미지 업로드 설정
  - 지원 파일 형식: jpg, svg, webp, png, gif
  - 최대 파일 크기: 5MB

### MinIO 설정 상세
#### 개발 환경
- SSL 비활성화
- 공개 읽기 접근 (public-read)
- 로컬 테스트용 설정

#### 프로덕션 환경
- SSL 활성화 필수
- 보안 강화 설정
  - ACL 제한
  - HTTPS 필수
  - 적절한 CORS 설정

### 환경별 주요 차이점
| 설정 | 개발 환경 | 프로덕션 환경 |
|------|-----------|---------------|
| SSL | 비활성화 | 활성화 |
| ACL | public-read | 제한적 |
| 도메인 | localhost:9000 | minio.도메인명 |
| 보안 | 최소화 | 강화 |

### 보안 주의사항
1. 프로덕션 환경 설정 시 주의사항
   - 기본 자격증명 변경 필수
   - SSL/TLS 인증서 설정
   - 적절한 버킷 정책 설정
   - 접근 로그 활성화
2. 파일 업로드 보안
   - 파일 크기 제한 (기본 5MB)
   - 허용된 파일 형식만 업로드
   - 악성 파일 검사 고려
