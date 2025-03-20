from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from enum import Enum
import pytz

# db 인스턴스를 여기서만 생성
db = SQLAlchemy()

# 한국 시간대 설정
korea_tz = pytz.timezone('Asia/Seoul')

def get_korea_time():
    """현재 한국 시간을 반환"""
    return datetime.now(korea_tz)

def utcnow_to_korea():
    """DB 기본값으로 사용하기 위한 형태로 한국 시간 반환 (timezone 없는 형태)"""
    return get_korea_time().replace(tzinfo=None)

def calculate_business_days(start_date, days=5):
    """주말을 제외한 영업일 기준으로 날짜 계산"""
    current_date = start_date
    remaining_days = days

    while remaining_days > 0:
        current_date += timedelta(days=1)
        # 월요일은 0, 일요일은 6
        if current_date.weekday() < 5:  # 0-4는 월-금
            remaining_days -= 1
    
    return current_date

class ProjectStatus(Enum):
    APPLICATION_COMPLETE = "application_complete"  # 신청 완료
    RECEPTION_COMPLETE = "reception_complete"      # 접수 완료
    POC_IN_PROGRESS = "poc_in_progress"           # POC 진행중
    DELAYED = "delayed"                           # 지연됨 (기존 delay에서 변경)
    POC_COMPLETE = "poc_complete"                 # POC 완료
    CANCELLED = "cancelled"                       # 취소됨

class EmailType(Enum):
    # 상태 변경과 연관된 이메일
    APPLICATION_COMPLETE = "application_complete"  # 신청 완료 메일 (ProjectStatus.APPLICATION_COMPLETE로 변경)
    SUBMISSION_COMPLETE = "submission_complete"    # 제출 완료 메일 (ProjectStatus.RECEPTION_COMPLETE로 변경)
    POC_COMPLETE = "poc_complete"                 # POC 완료 메일 (ProjectStatus.POC_COMPLETE로 변경)
    CANCELLATION = "cancellation"                 # 취소 안내 메일 (ProjectStatus.CANCELLED로 변경)
    
    # 상태 변경 없는 알림 이메일
    DELAY = "delay"                               # 기간 연장 메일 (상태 변경 없음)
    MISC = "misc"                                 # 기타 안내 메일 (상태 변경 없음)

class Project(db.Model):
    id = db.Column(db.String(20), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    company = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    project_type = db.Column(db.String(50), nullable=False)
    purpose = db.Column(db.Text, nullable=True)
    project_url = db.Column(db.String(200))
    status = db.Column(db.Enum(ProjectStatus), nullable=False, default=ProjectStatus.APPLICATION_COMPLETE)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow_to_korea)
    expected_report_date = db.Column(db.DateTime)
    cancel_reason = db.Column(db.Text)
    report_file = db.Column(db.String(200))  # 리포트 파일 경로

    def __repr__(self):
        return f'<Project {self.id}>'

    def __init__(self, **kwargs):
        super(Project, self).__init__(**kwargs)
        if not self.expected_report_date:
            start_date = get_korea_time()
            self.expected_report_date = calculate_business_days(start_date.date())

class StatusHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.String(36), db.ForeignKey('project.id'), nullable=False)
    previous_status = db.Column(db.Enum(ProjectStatus))
    new_status = db.Column(db.Enum(ProjectStatus), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow_to_korea)
    created_by = db.Column(db.String(100))  # 상태 변경자
    reason = db.Column(db.Text)  # 상태 변경 사유 (취소 사유, 연장 사유 등)

    project = db.relationship('Project', backref=db.backref('status_history', lazy=True))

class ProjectDiscussion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.String(36), db.ForeignKey('project.id'), nullable=False)
    topic = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow_to_korea)
    created_by = db.Column(db.String(100), nullable=False)

    project = db.relationship('Project', backref=db.backref('discussions', lazy=True))

class EmailHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.String(36), db.ForeignKey('project.id'), nullable=False)
    email_type = db.Column(db.Enum(EmailType), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    recipient = db.Column(db.String(120), nullable=False)
    status = db.Column(db.String(20), nullable=False)  # success, failed
    error_message = db.Column(db.Text)
    sent_at = db.Column(db.DateTime, nullable=False, default=utcnow_to_korea)
    
    project = db.relationship('Project', backref=db.backref('email_history', lazy=True))

class ProjectAction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.String(20), db.ForeignKey('project.id'), nullable=False)
    action_type = db.Column(db.String(50), nullable=False)  # 예: '접수 완료', '검토 완료' 등
    action_date = db.Column(db.DateTime, default=utcnow_to_korea)
    description = db.Column(db.Text, nullable=True)

    project = db.relationship('Project', backref='actions')
