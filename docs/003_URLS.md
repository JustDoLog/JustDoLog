# JustDoLog URL 구조

## 1. 인증 & 계정 관리 (`/accounts/`)

### 프로필 관리
| URL | 설명 | 메서드 | 인증필요 |
|-----|------|--------|----------|
| `/accounts/signup/` | 회원가입 | POST | x |
| `/accounts/login/` | 로그인 | POST | x |
| `/accounts/logout/` | 로그아웃 | POST | ✓ |
| `/accounts/profile/` | 로그인 사용자의 프로필 조회 | GET | ✓ |
| `/accounts/profile/edit/` | 프로필 정보 수정 (소셜 링크 등) | GET, POST | ✓ |
| `/accounts/delete/` | 계정 영구 삭제 | POST | ✓ |
| `/accounts/follow/<username>/` | 특정 사용자 팔로우/언팔로우 | POST | ✓ |

## 2. 블로그 & 포스트 관리 (`/@<username>/`)

### 블로그 관리
| URL | 설명 | 메서드 | 인증필요 |
|-----|------|--------|----------|
| `/@<username>/posts/` | 사용자의 블로그 메인 페이지 | GET | × |
| `/@<username>/posts/drafts/` | 임시저장된 포스트 목록 | GET | ✓ |

### 포스트 CRUD
| URL | 설명 | 메서드 | 인증필요 |
|-----|------|--------|----------|
| `/@<username>/posts/new/` | 새 포스트 작성 | GET, POST | ✓ |
| `/@<username>/posts/new/upload_image` | 포스트 이미지 업로드 | POST | ✓ |
| `/@<username>/posts/<slug>/` | 포스트 상세 보기 | GET | × |
| `/@<username>/posts/<slug>/edit/` | 포스트 수정 | GET, POST | ✓ |
| `/@<username>/posts/<slug>/delete/` | 포스트 삭제 | POST | ✓ |

### 포스트 상호작용
| URL | 설명 | 메서드 | 인증필요 |
|-----|------|--------|----------|
| `/@<username>/posts/<slug>/like/` | 좋아요 토글 (HTMX) | POST | ✓ |
| `/@<username>/posts/<slug>/read/` | 조회수 기록 (HTMX) | POST | ✓ |

## 3. 콘텐츠 탐색 (`/discovery/`)

### 포스트 피드
| URL | 설명 | 메서드 | 인증필요 |
|-----|------|--------|----------|
| `/discovery/trending/` | 인기 포스트 (최근 7일) | GET | × |
| `/discovery/recent/` | 최신 포스트 | GET | × |
| `/discovery/liked/` | 내가 좋아요한 포스트 | GET | ✓ |
| `/discovery/recent_read/` | 최근 읽은 포스트 | GET | ✓ |
| `/discovery/following/` | 팔로우 중인 블로거 포스트 | GET | ✓ |

### 검색 & 탐색
| URL | 설명 | 메서드 | 인증필요 |
|-----|------|--------|----------|
| `/discovery/bloggers/popular/` | 인기 블로거 목록 | GET | × |
| `/discovery/search/` | 전문 검색 (제목, 내용) | GET | × |
| `/discovery/tags/<tag_name>/` | 태그별 포스트 목록 | GET | × |

## 4. 시스템 & 유틸리티

### 관리자 & 유틸리티
| URL | 설명 | 메서드 | 인증필요 |
|-----|------|--------|----------|
| `/admin/` | 관리자 대시보드 | GET, POST | ✓ |
| `/tinymce/` | 리치 텍스트 에디터 | GET, POST | ✓ |
| `/media/` | 업로드된 미디어 파일 | GET | × |