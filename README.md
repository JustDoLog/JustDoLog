# JustDoLog

JustDoLog는 심플하고 강력한 블로깅 플랫폼입니다. WYSIWYG 지원과 코드 하이라이팅 기능을 통해 기술 문서 작성에 최적화되어 있으며, PostgreSQL의 전문 검색 기능을 활용한 강력한 검색 기능을 제공합니다.

## 주요 기능
- WYSIWYG 기반의 블로그 포스팅
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
- **Cache**
  - Reids 7.2
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
git clone https://github.com/JustDoLog/JustDoLog.git
cd JustDoLog
```

2. 환경 변수 설정
```bash
cp env.dev.example .env.dev
# .env.dev 파일을 적절히 수정하세요 (변경하시오 영역)
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

- 이제 http://localhost:8000 에서 개발 서버에 접속할 수 있습니다. 
- 관리자 페이지는 http://localhost:8000/admin/ 에서 확인할 수 있습니다.

6. 소셜 로그인(Google, Github)을 위한 "사이트 변경"
```bash
Admin/사이트/사이트들/example.com 수정 

도메인명: localhost:8000
표시명: localhost:8000
```

7. 소셜 로그인(Google, Github)을 위한 "소셜 어플리케이션" 등록 (.env.dev에 소셜계정정보가 입력된 후)
```bash
Admin/소셜계정/소셜 어플리케이션/추가

Provider: Google
이름: Google
클라이언트 아이디: .env.dev에 입력한 GOOGLE_CLIENT_ID 값
비밀 키: .env.dev에 입력한 GOOGLE_CLIENT_SECRET 값
Sites: 6번에서 변경한 localhost:8000을 선택된 사이트에 추가

----

Provider: Github
이름: Github
클라이언트 아이디: .env.dev에 입력한 GITHUB_CLIENT_ID 값
비밀 키: .env.dev에 입력한 GITHUB_CLIENT_SECRET 값
Sites: 6번에서 변경한 localhost:8000을 선택된 사이트에 추가
```

8. minio admin에서 비밀번호 변경
```bash
http://localhost:9000/
admin/miniosecret 로 로그인하여 admin 비밀번호 변경 및 "justdolog-media" 버킷 생성 확인
```

9. 테스트 계정 및 테스트 포스팅 생성 커맨드
```bash
docker-compose -f docker-compose.dev.yml exec web python manage.py generate_test_data
```

### 프로덕션 환경 설정
1. 저장소 클론
```bash
git clone https://github.com/JustDoLog/JustDoLog.git
cd JustDoLog
```

2. 환경 변수 설정
```bash
cp env.prd.example .env
# .env 파일을 프로덕션 환경에 맞게 수정하세요
```

3. 프로덕션 서버 실행
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

5. 관리자 계정 생성
```bash
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

- 이제 https://www.justdolog.com 에서 상용 서버에 접속할 수 있습니다. 
- 관리자 페이지는 https://www.justdolog.com/admin/ 에서 확인할 수 있습니다.

6. 소셜 로그인(Google, Github)을 위한 "사이트 변경"
```bash
Admin/사이트/사이트들/example.com 수정 

도메인명: justdolog.com
표시명: justdolog.com
```

7. 소셜 로그인(Google, Github)을 위한 "소셜 어플리케이션" 등록 (.env에 소셜계정정보가 입력된 후)
```bash
Admin/소셜계정/소셜 어플리케이션/추가

Provider: Google
이름: Google
클라이언트 아이디: .env.dev에 입력한 GOOGLE_CLIENT_ID 값
비밀 키: .env.dev에 입력한 GOOGLE_CLIENT_SECRET 값
Sites: 6번에서 변경한 justdolog.com을 선택된 사이트에 추가

----

Provider: Github
이름: Github
클라이언트 아이디: .env.dev에 입력한 GITHUB_CLIENT_ID 값
비밀 키: .env.dev에 입력한 GITHUB_CLIENT_SECRET 값
Sites: 6번에서 변경한 justdolog.com을 선택된 사이트에 추가
```

8. minio admin에서 버킷 생성 확인
```bash
https://minio.justdolog.com에 접속하여 로그인 후 "justdolog-media" 버킷 생성 확인
```

9. 테스트 계정 및 테스트 포스팅 생성 커맨드
```bash
docker-compose -f docker-compose.prod.yml exec web python manage.py generate_test_data
```

## 소셜 로그인 설정

### Google OAuth 설정
1. [Google Cloud Console](https://console.cloud.google.com/)에서 새 프로젝트 생성
2. OAuth 2.0 클라이언트 ID 생성
   - 승인된 리디렉션 URI: `http://localhost:8000/accounts/google/login/callback/`
3. 발급받은 클라이언트 ID와 시크릿을 `.env.dev`에 설정
   ```
   GOOGLE_CLIENT_ID=your-client-id
   GOOGLE_CLIENT_SECRET=your-client-secret
   ```

### GitHub OAuth 설정
1. [GitHub Developer Settings](https://github.com/settings/developers)에서 새 OAuth 앱 생성
2. Authorization callback URL: `http://localhost:8000/accounts/github/login/callback/`
3. 발급받은 클라이언트 ID와 시크릿을 `.env.dev`에 설정
   ```
   GITHUB_CLIENT_ID=your-client-id
   GITHUB_CLIENT_SECRET=your-client-secret
   ```

### Django Admin 설정
소셜 로그인을 사용하기 위해서는 Django Admin에서 추가 설정이 필요합니다:

1. 관리자 계정으로 Django Admin (`http://localhost:8000/admin`) 접속
2. Sites 섹션에서 기본 사이트의 도메인을 "localhost:8000"으로 변경
3. Social Applications 섹션에서 소셜 앱 추가
   - Google 설정:
     - Provider: Google
     - Name: Google
     - Client ID: .env.dev의 GOOGLE_CLIENT_ID 값
     - Secret key: .env.dev의 GOOGLE_CLIENT_SECRET 값
     - Sites: localhost:8000 선택
   - GitHub 설정:
     - Provider: GitHub
     - Name: GitHub
     - Client ID: .env.dev의 GITHUB_CLIENT_ID 값
     - Secret key: .env.dev의 GITHUB_CLIENT_SECRET 값
     - Sites: localhost:8000 선택

> **Note**: 환경 변수로 설정한 값을 Django Admin에서도 설정해야 하는 이유
> - Django allauth는 데이터베이스에 저장된 소셜 앱 설정을 우선적으로 사용
> - settings.py의 SOCIALACCOUNT_PROVIDERS는 기본값으로만 작동
> - 여러 소셜 앱 설정을 동적으로 관리하기 위한 설계

## 라이선스
이 프로젝트는 MIT 라이선스를 따릅니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참고하세요.