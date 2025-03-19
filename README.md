# POC Welcome Email Sender

이 시스템은 POC 신청 완료 후 자동으로 환영 이메일을 발송하는 Python 스크립트입니다.

## 설치 방법

1. 필요한 패키지 설치:
```bash
pip install -r requirements.txt
```

2. 환경 변수 설정:
- `.env` 파일을 열고 SMTP 서버 설정을 입력합니다:
  ```
  SMTP_HOST=smtp.gmail.com
  SMTP_PORT=587
  SMTP_USER=your-email@gmail.com
  SMTP_PASSWORD=your-app-specific-password
  SMTP_FROM=your-email@gmail.com
  ```

## 사용 방법

1. POC 신청 데이터를 다음과 같은 형식으로 준비합니다:
```
:로켓: POC 시작하기 요청
접수시각: 2025-03-18T23:50:31.523Z
이름
홍길동
회사명
알티엠
이메일
example@rtm.ai
연락처
010-1234-5678
과제목적
테스트
유형
image
프로젝트ID
0b0fad21-9b87-4438-8bc1-79c062b927f8
프로젝트관리페이지
https://poc-request.hubble-engine.rtm.ai/project/auth
```

2. 스크립트 실행:
```bash
python send_welcome_email.py
```

## 주의사항

- Gmail을 사용하는 경우, 앱 비밀번호를 생성하여 사용해야 합니다.
- 이메일 템플릿(`online-poc-email-welcome.html`)은 UTF-8 인코딩으로 저장되어야 합니다.
- 프로젝트 ID와 이메일 주소는 필수 입력 항목입니다. 