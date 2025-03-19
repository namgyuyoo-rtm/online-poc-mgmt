from app import create_app
from app.models import db, Project, ProjectStatus
from datetime import datetime
import pytz

app = create_app()

with app.app_context():
    # 기존 테이블 삭제 후 재생성
    db.drop_all()
    db.create_all()
    
    # 테이블 구조 확인
    print("\n테이블 컬럼 확인:")
    print(Project.__table__.columns.keys())
    
    # 테스트 데이터 생성
    test_project = Project(
        id="POC-20240325-001",
        name="김철수",
        company="테스트기업(주)",
        email="test@company.com",
        phone="010-1234-5678",
        project_type="불량 탐지",
        purpose="반도체 웨이퍼 불량 검출 POC 진행",
        project_url="http://example.com/project1",
        status=ProjectStatus.INITIAL_REQUEST
    )
    
    db.session.add(test_project)
    db.session.commit()
    
    # 생성된 데이터 확인
    project = Project.query.first()
    print("\n생성된 프로젝트 정보:")
    print(f"ID: {project.id}")
    print(f"이름: {project.name}")
    print(f"예상 완료일: {project.expected_report_date}")
