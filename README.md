# RTM AI POC 관리 시스템

RTM AI POC 관리 시스템은 AI POC(Proof of Concept) 프로젝트의 생명주기를 효율적으로 관리하고 이메일 커뮤니케이션을 자동화하는 웹 애플리케이션입니다.

## 주요 기능

- **프로젝트 관리**: POC 프로젝트의 전체 생명주기 관리 (신청, 접수, 진행, 완료, 취소)
- **이메일 자동화**: 다양한 프로젝트 상태에 맞는 이메일 템플릿과 자동 발송 기능
- **상태 추적**: 프로젝트 진행 상황을 실시간으로 추적하고 D-day 카운터 제공
- **보고서 관리**: POC 결과 보고서 업로드 및 관리
- **프로젝트 연장**: 지연된 프로젝트에 대한 기간 연장 및 알림 기능

## 프로젝트 상태

시스템은 프로젝트를 다음 상태로 관리합니다:

- **신청 완료(APPLICATION_COMPLETE)**: 고객이 POC 프로젝트를 신청한 상태
- **접수 완료(RECEPTION_COMPLETE)**: 프로젝트가 검토되고 접수된 상태
- **POC 진행 중(POC_IN_PROGRESS)**: POC가 진행 중인 상태
- **POC 지연(DELAYED)**: 예상 완료일을 초과하여 지연된 상태
- **POC 완료(POC_COMPLETE)**: POC가 완료되고 보고서가 제출된 상태(아직 안함)
- **취소됨(CANCELLED)**: 프로젝트가 취소된 상태

## 이메일 유형

시스템은 다음과 같은 이메일 유형을 제공합니다:

- **신청 완료(APPLICATION_COMPLETE)**: POC 신청 접수 확인
- **접수 완료(SUBMISSION_COMPLETE)**: POC 프로젝트 접수 확인 및 진행 일정 안내
- **POC 완료(POC_COMPLETE)**: POC 완료 및 결과 보고서 제공
- **지연(DELAY)**: POC 일정 지연 안내
- **취소(CANCELLATION)**: POC 취소 안내
- **기타(MISC)**: 기타 필요한 커뮤니케이션

## 기술 스택

- **백엔드**: Flask (Python)
- **프론트엔드**: HTML, CSS, JavaScript, Bootstrap
- **데이터베이스**: SQLite (개발), PostgreSQL (프로덕션은 준비안함)
- **이메일 서비스**: Gmail SMTP

## 설치 및 실행

### 사전 요구사항

- Python 3.8 이상
- pip (Python 패키지 관리자)

### 설치 과정

1. 저장소 클론:
```bash
git https://github.com/namgyuyoo-rtm/online-poc-mgmt.git
cd online-poc-mgmt
```

2. 가상 환경 생성 및 활성화:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. 의존성 설치:
```bash
pip install -r requirements.txt
```

4. 환경 변수 설정:
```bash
cp .env.example .env
# .env 파일을 편집하여 필요한 설정(이메일, 데이터베이스 등) 추가
```

5. 데이터베이스 초기화:
```bash
flask db upgrade
```

6. 개발 서버 실행:
```bash
flask run --debug

```

## 배포

프로덕션 환경에 배포하려면 다음 단계를 따르세요:

1. 환경 변수 설정 (FLASK_ENV=production)
2. 데이터베이스 설정 (PostgreSQL 권장)
3. WSGI 서버 설정 (Gunicorn/uWSGI)
4. 웹 서버 프록시 설정 (Nginx/Apache)

## 구성 및 사용자 정의

- `.env` 파일에서 시스템 설정 변경
- `app/templates/` 디렉토리에서 이메일 템플릿 수정
- `app/static/` 디렉토리에서 CSS, JS 파일 수정

## 개발자 정보

이 프로젝트는 RTM 팀에 의해 개발되었습니다. 