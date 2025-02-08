# 프로덕션 배포 마이그레이션 가이드

## 1. 도메인 설정

### 1.1 환경 변수 수정 (.env)
```bash
# 도메인 설정
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# MinIO 설정
MINIO_SERVER_URL="https://minio.yourdomain.com"  # SSL 적용 시
MINIO_BROWSER_REDIRECT_URL="https://minio-console.yourdomain.com"  # SSL 적용 시
MINIO_USE_SSL=True
```

### 1.2 Nginx 설정 수정 (nginx/nginx.conf)
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # SSL 설정 추가
    listen 443 ssl;
    ssl_certificate /etc/nginx/ssl/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/live/yourdomain.com/privkey.pem;
    
    # HTTP를 HTTPS로 리다이렉트
    if ($scheme != "https") {
        return 301 https://$host$request_uri;
    }

    # ... 나머지 설정 ...
}
```

## 2. SSL/TLS 설정

### 2.1 Let's Encrypt 인증서 발급
```bash
# Certbot 설치
apt-get update
apt-get install certbot python3-certbot-nginx

# 인증서 발급
certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

### 2.2 MinIO SSL 설정
- MinIO Console용 인증서 발급
```bash
certbot --nginx -d minio.yourdomain.com -d minio-console.yourdomain.com
```

## 3. 보안 설정

### 3.1 환경 변수 업데이트
```bash
# Django 보안 키 변경
DJANGO_SECRET_KEY=<새로운 보안 키 생성>

# 데이터베이스 비밀번호 변경
DB_PASSWORD=<새로운 강력한 비밀번호>

# MinIO 비밀번호 변경
MINIO_ROOT_PASSWORD=<새로운 강력한 비밀번호>
```

### 3.2 파이어월 설정
```bash
# 필요한 포트만 개방
- 80 (HTTP)
- 443 (HTTPS)
- 9000 (MinIO API)
- 9001 (MinIO Console)
```

## 4. 이메일 설정

### 4.1 SMTP 설정 (.env)
```bash
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@yourdomain.com
EMAIL_HOST_PASSWORD=your-app-specific-password
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

## 5. 데이터베이스 설정

### 5.1 PostgreSQL 백업 설정
```bash
# 자동 백업 스크립트 설정
0 0 * * * docker-compose -f docker-compose.prod.yml exec db pg_dump -U $DB_USER $DB_NAME > backup_$(date +\%Y\%m\%d).sql
```

## 6. 모니터링 설정

### 6.1 로그 모니터링
- Docker 로그 설정 (docker-compose.prod.yml)
```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

## 7. 성능 최적화

### 7.1 Nginx 캐시 설정
```nginx
# 정적 파일 캐싱
location /static/ {
    expires 30d;
    add_header Cache-Control "public, no-transform";
}

location /media/ {
    expires 30d;
    add_header Cache-Control "public, no-transform";
}
```

### 7.2 PostgreSQL 성능 튜닝
```bash
# postgresql.conf 설정 최적화
shared_buffers = 256MB
work_mem = 16MB
maintenance_work_mem = 256MB
effective_cache_size = 768MB
```

## 8. 배포 전 체크리스트

1. [ ] 모든 환경 변수가 프로덕션용으로 설정되었는지 확인
2. [ ] DEBUG=False 설정 확인
3. [ ] ALLOWED_HOSTS에 도메인 추가 확인
4. [ ] SSL 인증서 발급 및 설정 확인
5. [ ] 데이터베이스 백업 설정 확인
6. [ ] 이메일 설정 확인
7. [ ] 정적 파일 수집 실행
8. [ ] 데이터베이스 마이그레이션 실행
9. [ ] MinIO 버킷 접근 권한 설정 확인
10. [ ] 로그 설정 확인

## 9. 롤백 계획

### 9.1 데이터베이스 롤백
```bash
# 최신 백업에서 복원
docker-compose -f docker-compose.prod.yml exec db psql -U $DB_USER $DB_NAME < latest_backup.sql
```

### 9.2 이전 버전으로 롤백
```bash
# 이전 버전 태그로 롤백
git checkout <이전_버전_태그>
docker-compose -f docker-compose.prod.yml up -d --build
```

## 10. 유지보수 가이드

### 10.1 정기적인 작업
1. 데이터베이스 백업 확인 (매일)
2. 로그 모니터링 (매일)
3. SSL 인증서 갱신 확인 (매월)
4. 보안 업데이트 적용 (매월)
5. 성능 모니터링 및 최적화 (분기별)

### 10.2 장애 대응
1. 로그 확인: `docker-compose -f docker-compose.prod.yml logs`
2. 서비스 재시작: `docker-compose -f docker-compose.prod.yml restart <service_name>`
3. 전체 재배포: `docker-compose -f docker-compose.prod.yml up -d --build` 