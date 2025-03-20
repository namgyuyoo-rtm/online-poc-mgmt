from datetime import datetime, timedelta
from app.models import db, Project, ProjectStatus, StatusHistory, ProjectDiscussion, EmailHistory, EmailType, ProjectAction
from app.models import get_korea_time, utcnow_to_korea, korea_tz  # 한국 시간 유틸리티 함수 추가
from flask import Blueprint, render_template, jsonify, request, redirect, url_for, send_file, abort, current_app
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, URL
import asyncio
import jinja2
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from jinja2 import Template
import random
import logging
import pytz
from werkzeug.utils import secure_filename
import base64
import re
from flask_mail import Message

LOGO_BASE64 = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAG0AAAAmCAYAAADOZxX5AAAACXBIWXMAABCcAAAQnAEmzTo0AAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAgPSURBVHgB7VvdTtxGFD5nvLQlihpHCpCoKnGSVupdyBPEeYLAEwAXzd8N5AmAJ2C5qUhu2D4B5AnYPAHJXaWW4KRqy5/EVkrDhqzn9JzZXa9t7MWQ9bKR9pOI1+Oxx55v5pzvnJkA9PHFAbNWPJh1bP/jB5d8dFBh5RNA+drytgd9dB0nkrb76OoUEk0CwRgoXCJlrQ3/8tcr6OPcUEi7sPfoqstkrRCRA4jlGsKd/szqDSTOtL2HI4t8mJXfmnBh5Pn2PPTRMzhG2v7D4RUCnJLfBLA0/GxnFvroKURIC88wJsxjwm5AHz2HwKeJ4ACiYFYh4jT0CG5970ydVAct8HgEVn73vFOJJIdh+eDCGeFbsOZ5XiVefstxxsEHu/luf3heGc6A8LcPWFD+jRszpB08uur4RHMUVMXy0PJ2GXoEhLRyYh1dP94cvV5BoLUBpRbkA0+6T2laJwQHzogCoMeHcrycBdwK2zG78W5C6mU4JYSw8LcfaVzgw7ySEw16kglzggYRfoUvF7b45CNNWzdHRxfbVWyMYgfyANUJa74TtzUOp4WCyaRiM9OI6sKjVdnq2TgMEdb4fV8nlN8moDHuLCdUOntrdNTefPeujak3ozcO7nCaOalNAXegFy9ji2uz7I4WKvO8NciIHx1nzNfkhsvY/F83be4/GB6n2Gjr6eBZ44s3f3qltMs/OI6rxTQ1yJNZx6P85WbCPZspzxE/pzTMZG0zAXa8gAhcebesvs3XeiYt96F4GLnhAkwYOZ3E7pOhMcgR0ika8R5/SEscKJqELmIggTSB1jqTiZRBAxCzfnJ/wy8q9l+3oYtQ2sqVNIEnAoRwqXkuo/wn0xHdAaWQxkRMGtN5AtLUrEK6ZI5M31i2BjsDFj13oQtAgoiJr+UlOE4Hm83u1EmVWDHOJZY3uFFNWRp+8D8cAkBO4KntQhfAsVEFzgnkR/uUY95y6zfdb3ev+D0IDzAMuStqkpYAtsku5ACJB6k3RnzeiJDGLuhF8LshSNJuZL/X8r9CGLbMfBOK2Ts2IonycdxsoqbyFjpNRD6+3nbXFDFZEdI8FhClsDDi/k00f8cECBOGfoQfR/5RkenXgnvQYRMpi6iyLkf1DEKuqI/k1scjYCkp1ZQbdHSmmbZjwihJkBSMzG/hq5S4TvHIf5l0oUbUNptwWujqhxkxjRwAv4acIGRJFkRzaipcPqBgAc4J2JgUWkExXK60PrZ6ogGDkEAGmqThJG8ZriMqmHUBpkXp4/uPr3bETMqCKq/LzZuXSW/vVLg56sxynnEr9Ed1sjDSGahwOksOspNI8tsy28KChN8sMqviKTVU6alEVahWXyX5NdO4puLuk+8+K646+HloDDWtmufxu3cqEc0jt9RIGDiQ0EnSQUrhvU3vVJmMXMGzLjzj7YggCecZsbUqUItpgKqEDZdLlYrs/YBk2OjXNrYfjJxpIXT/8dCkj0qy6HbjrTtmpmTkWogTkcwH1M2KIeutd++syyGfC/Y514MTavlw8z4hDdEUJCJA+LfbLMc2/VQQ0syParWYNtsEFsIiL5Cui5mDDNjl2SX1SatSkzCzqLq8XYIOwqydxT8QyT4vsjKBMDB7IkgkMcz+raUmmdSYdYjwIgG2yfLLbGNCJvgp622ac/m6u/9wxOMb11DRS40Dnq9981BLWTbWai43eh8S4jxf8oE54I3nFW9dd+7ySDVOnDtiXPzdm3deEc4J/C6BMuS+ehu+JoJEESejG4FyjQUJz6z70FgUQAr7vbpFYX/dKvAbM01gfE0G89VwsrOkcVVMZ4FoS/7kNxMmitM9dg+vgue5k8tHmI6GLjQnIxjOD6mpwIb8D2Ybm/PJ8NpbFqVrSJOYbO/B8BwTN9+WODGhfP394ODloWc7WEO8Yeq3Ma187amYRdl/IrEa5IDAv7Vg81rUapbkbC6IpgaP9Y1SyfEXC5VyitINymSV3ZBmYjLE+SZxMjMoplrkvKbwDtvT0sXDwznxWTzDZuRcyuPEmfvZJA493ynKDi8umq19OJyCnGD8m8KnoSLH0rqjsWZmhGYOJgxo8blR+d+snCoII6ibx5a6m2cyVjn3WBYfxOQF01gpeqpQy2rqBtR3bLlyZMI3jD8Dmm69Myz9NzgoBHv8vI3mljzu1FxHvvi3cGdIu+Lf4DyRlrhGWIqdiwBJi2FDz9B1n8ajIZylGPdZkFhMCpu1KWMC2cRZpF5ZGhcpYVVA+bVV68KFstQT0yl7Jb89PJxsEBz4FupC3pH920Tcv3VzLc2JtYWQTJohKBSutJP5fK1VD9QlQ1o8KyJiQ7aEs1LcknMxcZ+YxLQMvZT71eq41LtYrY7JfZwkLYYJFsL8hF1LnYb4NxXd/mcfcabk3PxbO4TykQNt+4YixBvJL8qRzZgQNx6pymQU6kR5TGLbdSCGLG6WIIVcns1L156dTUGyDA5IkL1/J9UXn8HZhnu8ruU0y76pK7qsSePKadtMu7fQxrqI/Ld8E3xX2qXaUHydDpZ3KsHOkYMp26598/UqM+U2y2R2DLBvulz0OI4bWQ9fS3hw6cry9rQJwGPxXv//A3QWQZwmAfbQ8o6IDxkla+ZP6wkhTK6zU3/b7kGa6F85yqw1z2BBwMeSKMg+YZ0FZq24J/nHevCc/CCyJq48/7sjGfw+2kNlrVg4+lhKU39S3iese8hMmlkNYHOZFHTnlVfsIxmZzWMTslPLMoE18ToZeO8vDJZuFLu4lN8H/A88yJ7V1te3qQAAAABJRU5ErkJggg=='

# 중앙화된 이메일 설정
EMAIL_CONFIG = {
    # 상태 변경과 연관된 이메일
    EmailType.APPLICATION_COMPLETE: {
        'template': 'email/online-poc-email-welcome.html',
        'subject': 'RTM AI POC 신청 완료 안내',
        'page_template': 'application_complete.html',
        'target_status': ProjectStatus.APPLICATION_COMPLETE,
        'allowed_from_statuses': []  # 빈 배열은 신규 프로젝트 생성 가능 (기존 프로젝트 ID가 없을 때)
    },
    EmailType.SUBMISSION_COMPLETE: {
        'template': 'email/online-poc-email-complete.html',
        'subject': 'RTM AI POC 제출 완료 안내',
        'page_template': 'submission_complete.html',
        'target_status': ProjectStatus.RECEPTION_COMPLETE,
        'allowed_from_statuses': [ProjectStatus.APPLICATION_COMPLETE]
    },
    EmailType.POC_COMPLETE: {
        'template': 'email/online-poc-email-report.html',
        'subject': 'RTM AI POC 완료 안내',
        'page_template': 'submission_complete.html',  # 임시로 존재하는 템플릿 활용
        'target_status': ProjectStatus.POC_COMPLETE,
        'allowed_from_statuses': [ProjectStatus.RECEPTION_COMPLETE, ProjectStatus.POC_IN_PROGRESS, ProjectStatus.DELAYED]
    },
    EmailType.CANCELLATION: {
        'template': 'email/online-poc-email-cancel.html',
        'subject': 'RTM AI POC 취소 안내',
        'page_template': 'email_history.html',  # 임시로 존재하는 템플릿 활용
        'target_status': ProjectStatus.CANCELLED,
        'allowed_from_statuses': [ProjectStatus.APPLICATION_COMPLETE, ProjectStatus.RECEPTION_COMPLETE, 
                                ProjectStatus.POC_IN_PROGRESS, ProjectStatus.DELAYED, ProjectStatus.POC_COMPLETE]
    },
    
    # 상태 변경 없는 알림 이메일 (상태 검증은 하지만 변경하지 않음)
    EmailType.DELAY: {
        'template': 'email/online-poc-email-delay.html',
        'subject': 'RTM AI POC 기간 연장 안내',
        'page_template': 'application_complete.html',  # 임시로 존재하는 템플릿 활용
        'allowed_from_statuses': [ProjectStatus.RECEPTION_COMPLETE, ProjectStatus.POC_IN_PROGRESS]
    },
    EmailType.MISC: {
        'template': 'email/online-poc-email-misc.html',
        'subject': 'RTM AI POC 안내',
        'page_template': 'email_history.html',  # 임시로 존재하는 템플릿 활용
        'allowed_from_statuses': []  # 모든 상태에서 전송 가능
    }
}

# 로깅 설정
log_format = '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
logging.basicConfig(level=logging.INFO, format=log_format)
logger = logging.getLogger(__name__)

bp = Blueprint('main', __name__)

# 유틸리티 함수
async def send_email(project, email_type, additional_data=None):
    """
    중앙화된 이메일 발송 함수
    
    Args:
        project: 프로젝트 객체
        email_type: EmailType 객체
        additional_data: 템플릿에 전달할 추가 데이터 (선택사항)
        
    Returns:
        (성공 여부, 오류 메시지)
    """
    try:
        logger.info(f"이메일 발송 시작: {project.email}, {email_type}")
        
        if email_type not in EMAIL_CONFIG:
            logger.error(f"지원되지 않는 이메일 타입: {email_type}")
            return False, "지원되지 않는 이메일 타입"
        
        config = EMAIL_CONFIG[email_type]
        
        # 프로젝트 상태 검증
        if 'allowed_from_statuses' in config and config['allowed_from_statuses']:
            # 허용된 상태 목록이 있고 비어있지 않은 경우 검증
            if project.status not in config['allowed_from_statuses']:
                allowed_statuses = ', '.join([status.value for status in config['allowed_from_statuses']])
                logger.error(f"{email_type.value} 이메일은 {allowed_statuses} 상태에서만 발송 가능합니다. 현재 상태: {project.status.value}")
                return False, f"현재 상태({project.status.value})에서는 이메일을 발송할 수 없습니다"
        
        # 이메일 생성
        msg = MIMEMultipart('alternative')
        msg['Subject'] = config['subject']
        msg['From'] = os.getenv('SMTP_FROM')
        msg['To'] = project.email
        
        # 템플릿 데이터 준비
        data = {
            'name': project.name,
            'company': project.company,
            'email': project.email,
            'phone': project.phone,
            'project_type': project.project_type,
            'project_id': project.id,
            '프로젝트관리페이지': os.getenv('APP_URL', 'http://localhost:5000') + f'/project/{project.id}',
            'purpose': project.purpose or '',
            '로고': LOGO_BASE64
        }
        
        # 접수시각 정보 추가 (None이 아닌 경우에만)
        if project.created_at:
            data['접수시각'] = project.created_at.strftime('%Y-%m-%d %H:%M')
        else:
            # 현재 시각 사용
            data['접수시각'] = get_korea_time().strftime('%Y-%m-%d %H:%M')
        
        # 추가 데이터가 있으면 병합
        if additional_data:
            data.update(additional_data)
        
        # 템플릿 렌더링
        template_path = f'app/templates/{config["template"]}'
        # 파일이 존재하지 않으면 앱 루트의 템플릿 디렉토리 확인
        if not os.path.exists(template_path):
            template_path = f'templates/{config["template"]}'
            if not os.path.exists(template_path):
                logger.error(f"템플릿 파일을 찾을 수 없습니다: {config['template']}")
                return False, f"템플릿 파일을 찾을 수 없습니다: {config['template']}"
                
        with open(template_path, 'r', encoding='utf-8') as f:
            template = Template(f.read())
        
        html_content = template.render(**data)
        msg.attach(MIMEText(html_content, 'html'))
        
        # 이메일 전송
        smtp = aiosmtplib.SMTP(
            hostname=os.getenv('SMTP_HOST'),
            port=int(os.getenv('SMTP_PORT')),
            use_tls=os.getenv('SMTP_SECURE', 'true').lower() == 'true'
        )
        
        await smtp.connect()
        await smtp.login(os.getenv('SMTP_USER'), os.getenv('SMTP_PASSWORD'))
        await smtp.send_message(msg)
        await smtp.quit()
        
        # 이메일 발송 이력 저장
        history = EmailHistory(
            project_id=str(project.id),
            email_type=email_type,
            subject=config['subject'],
            recipient=project.email,
            status='success'
        )
        db.session.add(history)
        db.session.commit()
        
        logger.info(f"이메일 발송 성공: {project.email}, {email_type}")
        return True, None
        
    except Exception as e:
        logger.error(f"이메일 발송 실패: {str(e)}")
        
        # 실패 이력 저장
        try:
            history = EmailHistory(
                project_id=str(project.id),
                email_type=email_type,
                subject=config['subject'] if 'config' in locals() else f"이메일 ({email_type})",
                recipient=project.email,
                status='failed',
                error_message=str(e)
            )
            db.session.add(history)
            db.session.commit()
        except Exception as e2:
            logger.error(f"이메일 이력 저장 실패: {str(e2)}")
        
        return False, str(e)

class EmailForm(FlaskForm):
    name = StringField('이름', validators=[DataRequired()])
    company = StringField('회사명', validators=[DataRequired()])
    email = StringField('이메일', validators=[DataRequired(), Email()])
    phone = StringField('연락처', validators=[DataRequired()])
    project_type = StringField('유형', validators=[DataRequired()])
    project_id = StringField('프로젝트 ID', validators=[DataRequired()])
    project_url = StringField('프로젝트 관리페이지', validators=[DataRequired(), URL()])
    purpose = TextAreaField('과제목적', validators=[])
    submit = SubmitField('메일 보내기')

class POCRequestForm(FlaskForm):
    name = StringField('이름', validators=[DataRequired()])
    company = StringField('회사명', validators=[DataRequired()])
    email = StringField('이메일', validators=[DataRequired(), Email()])
    phone = StringField('연락처', validators=[DataRequired()])
    project_type = StringField('유형', validators=[DataRequired()])
    project_id = StringField('프로젝트 ID', validators=[DataRequired()])
    project_url = StringField('프로젝트 관리페이지', validators=[DataRequired(), URL()])
    purpose = TextAreaField('과제목적', validators=[])
    submit = SubmitField('미리보기')

@bp.route('/')
def index():
    return redirect(url_for('main.main'))

@bp.route('/main')
def main():
    # 최근 생성된 10개의 프로젝트 조회
    projects = Project.query.order_by(Project.created_at.desc()).limit(10).all()
    # 오늘 날짜를 템플릿에 전달
    today = datetime.now().date()
    return render_template('main.html', projects=projects, today=today)

@bp.route('/submission-complete', methods=['GET', 'POST'])
async def submission_complete():
    form = POCRequestForm()
    email_type = EmailType.SUBMISSION_COMPLETE
    preview_url = EMAIL_CONFIG[email_type]['template']
    
    if form.validate_on_submit():
        # 기존 프로젝트 확인
        existing_project = Project.query.get(form.project_id.data)
        
        if existing_project:
            # 기존 프로젝트가 있으면 상태 업데이트
            if existing_project.status not in EMAIL_CONFIG[email_type]['allowed_from_statuses']:
                # 허용되지 않은 상태면 오류 반환
                return render_template('submission_complete.html', 
                                     form=form, 
                                     preview_url=preview_url,
                                     error=f"현재 상태({existing_project.status.value})에서는 제출 완료 처리를 할 수 없습니다.")
            
            # 상태 변경
            old_status = existing_project.status
            existing_project.status = EMAIL_CONFIG[email_type]['target_status']
            
            # 상태 변경 이력 저장
            status_history = StatusHistory(
                project_id=existing_project.id,
                previous_status=old_status,
                new_status=existing_project.status,
                created_by='System',
                reason='제출 완료 처리'
            )
            db.session.add(status_history)
            
            # 이메일 발송
            success, error = await send_email(
                project=existing_project,
                email_type=email_type
            )
        else:
            # 새 프로젝트 생성
            new_project = Project(
                id=form.project_id.data,
                name=form.name.data,
                company=form.company.data,
                email=form.email.data,
                phone=form.phone.data,
                project_type=form.project_type.data,
                purpose=form.purpose.data,
                project_url=form.project_url.data,
                status=ProjectStatus.APPLICATION_COMPLETE  # 신규 프로젝트는 항상 APPLICATION_COMPLETE 상태로 생성
            )
            db.session.add(new_project)
            
            # 이메일 발송
            success, error = await send_email(
                project=new_project,
                email_type=email_type
            )
        
        db.session.commit()
        
        if not success:
            return render_template('submission_complete.html', form=form, preview_url=preview_url, error=error)
        
        return redirect(url_for('main.projects'))

    return render_template('submission_complete.html', form=form, preview_url=preview_url)

@bp.route('/application-complete', methods=['GET', 'POST'])
async def application_complete():
    form = POCRequestForm()
    email_type = EmailType.APPLICATION_COMPLETE
    preview_url = EMAIL_CONFIG[email_type]['template']
    
    if form.validate_on_submit():
        # 기존 프로젝트 확인
        existing_project = Project.query.get(form.project_id.data)
        
        if existing_project:
            # 기존 프로젝트가 있는 경우
            old_status = existing_project.status
            
            # 이메일 발송
            success, error = await send_email(
                project=existing_project,
                email_type=email_type
            )
            
            # 이메일 발송 성공한 경우에만 상태 업데이트
            if success:
                existing_project.status = EMAIL_CONFIG[email_type]['target_status']
                
                # 상태 변경 이력 저장
                status_history = StatusHistory(
                    project_id=existing_project.id,
                    previous_status=old_status,
                    new_status=existing_project.status,
                    created_by='System',
                    reason='신청 완료 처리'
                )
                db.session.add(status_history)
                db.session.commit()
                logger.info(f"프로젝트 {existing_project.id} 상태가 {EMAIL_CONFIG[email_type]['target_status'].value}로 업데이트되었습니다.")
                return redirect(url_for('main.projects'))
            else:
                db.session.rollback()
                logger.error(f"이메일 발송 실패로 상태 변경 없음: {error}")
                return render_template('application_complete.html', form=form, preview_url=preview_url, error=f"이메일 발송 실패: {error}")
        else:
            # 새 프로젝트 생성
            new_project = Project(
                id=form.project_id.data,
                name=form.name.data,
                company=form.company.data,
                email=form.email.data,
                phone=form.phone.data,
                project_type=form.project_type.data,
                purpose=form.purpose.data,
                project_url=form.project_url.data,
                status=ProjectStatus.APPLICATION_SUBMITTED  # 초기 상태는 신청 제출로 설정
            )
            
            # 세션에 추가하지만 아직 커밋하지 않음
            db.session.add(new_project)
            
            # 이메일 발송
            success, error = await send_email(
                project=new_project,
                email_type=email_type
            )
            
            # 이메일 발송 성공한 경우에만 커밋하고 상태 업데이트
            if success:
                # 상태 업데이트
                old_status = new_project.status
                new_project.status = EMAIL_CONFIG[email_type]['target_status']
                
                # 상태 변경 이력 저장
                status_history = StatusHistory(
                    project_id=new_project.id,
                    previous_status=old_status,
                    new_status=new_project.status,
                    created_by='System',
                    reason='신청 완료 처리'
                )
                db.session.add(status_history)
                
                # 변경사항 저장
                db.session.commit()
                logger.info(f"신규 프로젝트 {new_project.id} 생성 및 상태 {new_project.status.value}로 설정되었습니다.")
                return redirect(url_for('main.projects'))
            else:
                # 이메일 발송 실패 시 롤백, 프로젝트 생성 취소
                db.session.rollback()
                logger.error(f"이메일 발송 실패로 프로젝트 생성 취소: {error}")
                return render_template('application_complete.html', form=form, preview_url=preview_url, error=f"이메일 발송 실패: {error}")

    return render_template('application_complete.html', form=form, preview_url=preview_url)

@bp.route('/projects')
def projects():
    try:
        # 로깅 추가
        projects = Project.query.order_by(Project.created_at.desc()).all()
        logging.info(f"Found {len(projects)} projects")
        
        # 날짜 형식이 문자열이 아닌 경우를 처리
        for project in projects:
            if project.created_at:
                project.created_at = project.created_at.replace(tzinfo=None)
            if project.expected_report_date:
                project.expected_report_date = project.expected_report_date.replace(tzinfo=None)
        
        # 오늘 날짜를 템플릿에 전달
        today = datetime.now().date()
        return render_template('projects.html', projects=projects, today=today)
    except Exception as e:
        logging.error(f"Error in projects route: {str(e)}")
        # 오류 발생 시 빈 프로젝트 리스트로 렌더링
        return render_template('projects.html', projects=[])

@bp.route('/preview', methods=['GET', 'POST'])
@bp.route('/preview/<email_type>', methods=['GET', 'POST'])
def preview(email_type=None):
    if request.method == 'GET':
        return render_template('preview.html')
        
    form_data = request.get_json()
    form_data['접수시각'] = get_korea_time().strftime('%Y-%m-%d %H:%M:%S')
    
    # 이메일 템플릿 렌더링
    template_loader = jinja2.FileSystemLoader(searchpath='app/templates')
    template_env = jinja2.Environment(loader=template_loader)
    
    # 이메일 타입에 따른 템플릿 선택
    # 원래 URL 형식과의 호환성 위해 매핑 테이블 사용
    template_paths = {
        # 하이픈 형식 URL (기존 호환성)
        'submission-complete': 'email/online-poc-email-complete.html',
        'application-complete': 'email/online-poc-email-welcome.html',
        'cancellation': 'email/online-poc-email-cancel.html',
        'delay': 'email/online-poc-email-delay.html',
        'poc-complete': 'email/online-poc-email-report.html',
        
        # 언더스코어 형식 URL (새 형식)
        'submission_complete': 'email/online-poc-email-complete.html',
        'application_complete': 'email/online-poc-email-welcome.html',
        'cancellation': 'email/online-poc-email-cancel.html',
        'delay': 'email/online-poc-email-delay.html',
        'poc_complete': 'email/online-poc-email-report.html',
        'misc': 'email/online-poc-email-misc.html'
    }
    
    # URL에 이메일 타입이 없으면 기본값으로 application_complete 사용
    if email_type is None:
        email_type = 'application_complete'
    
    # 템플릿 경로 가져오기
    template_path = template_paths.get(email_type)
    if not template_path:
        # email_type에 해당하는 템플릿이 없으면 EmailType enum에서 찾기 시도
        try:
            # 하이픈이 있는 경우 언더스코어로 변환
            enum_key = email_type.replace('-', '_')
            
            # 대소문자 구분 없이 EmailType에서 찾기
            email_type_enum = None
            for et in EmailType:
                if et.value.lower() == enum_key.lower():
                    email_type_enum = et
                    break
            
            if email_type_enum and email_type_enum in EMAIL_CONFIG:
                template_path = EMAIL_CONFIG[email_type_enum]['template']
        except Exception as e:
            logger.error(f"이메일 미리보기 변환 중 오류: {str(e)}")
            pass
        
    if not template_path:
        return jsonify({'error': 'Invalid email type'}), 400
        
    # 기본 이메일 템플릿이 없는 경우 생성
    if 'misc' in email_type and not os.path.exists(f'app/templates/{template_path}'):
        try:
            # misc 이메일 템플릿이 없으면 기본 템플릿 복사
            default_path = 'app/templates/email/online-poc-email-welcome.html'
            with open(default_path, 'r', encoding='utf-8') as f:
                default_content = f.read()
            
            # 새 misc 템플릿 생성
            os.makedirs(os.path.dirname(f'app/templates/{template_path}'), exist_ok=True)
            with open(f'app/templates/{template_path}', 'w', encoding='utf-8') as f:
                f.write(default_content.replace('신청 완료', '안내'))
            
            logger.info(f"새 misc 이메일 템플릿 생성: {template_path}")
        except Exception as e:
            logger.error(f"misc 이메일 템플릿 생성 중 오류: {str(e)}")
    
    try:
        template = template_env.get_template(template_path)
        html_content = template.render(**form_data)
        return html_content
    except Exception as e:
        logger.error(f"이메일 미리보기 렌더링 중 오류: {str(e)}")
        return jsonify({'error': f'Template rendering error: {str(e)}'}), 500

@bp.route('/send', methods=['POST'])
async def send_email_form():
    """HTML 양식에서 이메일을 발송합니다."""
    try:
        data = request.get_json()
        logger.info(f"/send 요청: {data}")
        
        # 헤더에서 페이지 소스 확인
        source_page = request.headers.get('X-Source-Page', 'unknown')
        logger.info(f"소스 페이지: {source_page}")
        
        # 이메일 타입 확인
        email_type_str = data.get('email_type', '')
        if not email_type_str:
            # 이전 버전 호환성: 페이지 소스로부터 이메일 타입 유추
            if source_page == 'application-complete':
                email_type_str = 'application_complete'
            elif source_page == 'submission-complete':
                email_type_str = 'submission_complete'
            else:
                # 기본 페이지에 따라 이메일 타입 설정
                email_type_str = source_page.replace('-', '_') if '-' in source_page else source_page
        
        try:
            email_type = EmailType(email_type_str)
        except (ValueError, KeyError):
            try:
                email_type = EmailType[email_type_str.upper()]
            except (ValueError, KeyError):
                logger.error(f"유효하지 않은 이메일 타입: {email_type_str}")
                return jsonify({
                    'success': False,
                    'message': f'유효하지 않은 이메일 타입: {email_type_str}'
                }), 400
        
        # 필수 필드 확인
        required_fields = ['name', 'company', 'email', 'project_id']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            logger.error(f"필수 필드 누락: {', '.join(missing_fields)}")
            return jsonify({
                'success': False,
                'message': f"필수 필드가 누락되었습니다: {', '.join(missing_fields)}"
            }), 400
        
        # 프로젝트 ID로 기존 프로젝트 조회
        project = Project.query.filter_by(id=data['project_id']).first()
        additional_data = {}
        
        if email_type == EmailType.APPLICATION_COMPLETE:
            # 신규 프로젝트 생성 또는 기존 프로젝트 업데이트
            if not project:
                # 신규 프로젝트 생성
                project = Project(
                    id=data['project_id'],
                    name=data['name'],
                    company=data['company'],
                    email=data['email'],
                    phone=data.get('phone', ''),
                    project_type=data.get('project_type', ''),
                    purpose=data.get('purpose', ''),
                    project_url=data.get('project_url', ''),
                    status=ProjectStatus.APPLICATION_COMPLETE
                )
                db.session.add(project)
                
                # 상태 이력 추가
                status_history = StatusHistory(
                    project_id=data['project_id'],
                    previous_status=None,
                    new_status=ProjectStatus.APPLICATION_COMPLETE,
                    created_by='System',
                    reason='신규 프로젝트 생성'
                )
                db.session.add(status_history)
                
                logger.info(f"신규 프로젝트 생성: {data['project_id']}")
            else:
                # 기존 프로젝트 정보 업데이트 (신청 완료 이메일 재발송인 경우에만)
                application_complete_emails = EmailHistory.query.filter_by(
                    project_id=data['project_id'],
                    email_type=EmailType.APPLICATION_COMPLETE,
                    status='success'
                ).all()
                
                if len(application_complete_emails) > 0:
                    logger.warning(f"프로젝트 {data['project_id']}에 이미 신청 완료 이메일이 발송되었습니다.")
                    return jsonify({
                        'success': False,
                        'message': '해당 프로젝트에 이미 신청 완료 이메일이 발송되었습니다.'
                    }), 400
                
                old_status = project.status
                project.name = data['name']
                project.company = data['company']
                project.email = data['email']
                if 'phone' in data:
                    project.phone = data['phone']
                if 'project_type' in data:
                    project.project_type = data['project_type']
                if 'purpose' in data:
                    project.purpose = data['purpose']
                if 'project_url' in data:
                    project.project_url = data['project_url']
                
                # 상태 검증
                if project.status != ProjectStatus.APPLICATION_COMPLETE:
                    # 상태 이력 추가
                    status_history = StatusHistory(
                        project_id=data['project_id'],
                        previous_status=old_status,
                        new_status=ProjectStatus.APPLICATION_COMPLETE,
                        created_by='System',
                        reason='신청 완료 이메일 재발송으로 인한 상태 변경'
                    )
                    db.session.add(status_history)
                    
                    # 상태 업데이트
                    project.status = ProjectStatus.APPLICATION_COMPLETE
                    logger.info(f"프로젝트 상태 업데이트: {old_status} -> {ProjectStatus.APPLICATION_COMPLETE}")
            
            # 접수 시각 추가 데이터
            submission_time = data.get('submission_time', None)
            if submission_time:
                additional_data['접수시각'] = submission_time
        
        elif email_type == EmailType.SUBMISSION_COMPLETE:
            # 제출 완료 이메일: 기존 프로젝트 필요
            if not project:
                logger.error(f"프로젝트를 찾을 수 없음: {data['project_id']}")
                return jsonify({
                    'success': False,
                    'message': f"프로젝트를 찾을 수 없습니다: {data['project_id']}"
                }), 404
            
            # 기존 application_complete 이메일이 없는 경우 에러
            application_complete_emails = EmailHistory.query.filter_by(
                project_id=data['project_id'],
                email_type=EmailType.APPLICATION_COMPLETE,
                status='success'
            ).all()
            
            # 신청 완료 이메일이 없으면 에러
            if len(application_complete_emails) == 0:
                logger.warning(f"프로젝트 {data['project_id']}에 신청 완료 이메일이 발송되지 않았습니다.")
                return jsonify({
                    'success': False,
                    'message': '해당 프로젝트에 신청 완료 이메일이 먼저 발송되어야 합니다.'
                }), 400
            
            # 제출 완료 이메일이 이미 있는 경우 에러
            submission_complete_emails = EmailHistory.query.filter_by(
                project_id=data['project_id'],
                email_type=EmailType.SUBMISSION_COMPLETE,
                status='success'
            ).all()
            
            if len(submission_complete_emails) > 0:
                logger.warning(f"프로젝트 {data['project_id']}에 이미 제출 완료 이메일이 발송되었습니다.")
                return jsonify({
                    'success': False,
                    'message': '해당 프로젝트에 이미 제출 완료 이메일이 발송되었습니다.'
                }), 400
            
            # 상태 확인 (APPLICATION_COMPLETE 상태에서만 RECEPTION_COMPLETE로 변경 가능)
            if project.status != ProjectStatus.APPLICATION_COMPLETE:
                logger.warning(f"프로젝트 {data['project_id']}의 현재 상태 {project.status.value}에서는 제출 완료 이메일을 발송할 수 없습니다.")
                return jsonify({
                    'success': False,
                    'message': f'현재 프로젝트 상태 ({project.status.value})에서는 제출 완료 이메일을 발송할 수 없습니다.'
                }), 400
        
        else:
            # 기타 이메일 타입: 기존 프로젝트 필요
            if not project:
                logger.error(f"프로젝트를 찾을 수 없음: {data['project_id']}")
                return jsonify({
                    'success': False,
                    'message': f"프로젝트를 찾을 수 없습니다: {data['project_id']}"
                }), 404
        
        # 이메일 발송 전 DB 저장
        db.session.commit()
        
        # 이메일 준비 및 발송
        subject, html_content = prepare_email_content(project, email_type, additional_data)
        
        if not subject or not html_content:
            logger.error(f"이메일 콘텐츠 생성 중 오류 발생: {email_type.value}")
            return jsonify({
                'success': False,
                'message': '이메일 콘텐츠 생성 중 오류가 발생했습니다.'
            }), 500
        
        # 이메일 발송
        success, error_message = await send_mail(
            to_email=data['email'],
            subject=subject,
            html_content=html_content
        )
        
        # 이메일 이력 저장
        email_history = EmailHistory(
            project_id=data['project_id'],
            email_type=email_type,
            subject=subject,
            recipient=data['email'],
            status='success' if success else 'failed',
            error_message=error_message if not success else None,
            sent_at=utcnow_to_korea()
        )
        db.session.add(email_history)
        
        # 이메일 발송 성공 시 상태 업데이트
        if success:
            if email_type == EmailType.SUBMISSION_COMPLETE:
                old_status = project.status
                project.status = ProjectStatus.RECEPTION_COMPLETE
                
                # 상태 이력 추가
                status_history = StatusHistory(
                    project_id=data['project_id'],
                    previous_status=old_status,
                    new_status=ProjectStatus.RECEPTION_COMPLETE,
                    created_by='System',
                    reason='제출 완료 이메일 발송으로 인한 자동 상태 변경'
                )
                db.session.add(status_history)
                logger.info(f"프로젝트 상태 업데이트: {old_status} -> {ProjectStatus.RECEPTION_COMPLETE}")
        
        db.session.commit()
        
        if not success:
            logger.error(f"이메일 발송 실패: {error_message}")
            return jsonify({
                'success': False,
                'message': f'이메일 발송 실패: {error_message}'
            }), 500
        
        return jsonify({
            'success': True,
            'message': '이메일이 성공적으로 발송되었습니다.',
            'project_id': data['project_id'],
            'email_type': email_type.value
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"이메일 발송 중 오류: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'이메일 발송 중 오류가 발생했습니다: {str(e)}'
        }), 500

@bp.route('/email-history')
def email_history():
    try:
        # 이메일 발송 이력을 최신순으로 조회
        history = EmailHistory.query.order_by(EmailHistory.sent_at.desc()).all()
        return render_template('email_history.html', history=history)
    except Exception as e:
        logging.error(f"Error fetching email history: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/update-status/<project_id>', methods=['POST'])
def update_status(project_id):
    try:
        data = request.get_json()
        project = Project.query.get(project_id)
        if not project:
            return jsonify({'success': False, 'message': '프로젝트를 찾을 수 없습니다.'}), 404
        
        project.status = ProjectStatus(data['status'])
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@bp.route('/project/<project_id>')
def project_detail(project_id):
    try:
        project = Project.query.get(project_id)
        if not project:
            return jsonify({'success': False, 'message': '프로젝트를 찾을 수 없습니다.'}), 404
        
        # 오늘 날짜를 템플릿에 전달 (YYYY-MM-DD 형식)
        today = get_korea_time().strftime('%Y-%m-%d')
        
        return render_template('project_detail.html', project=project, today=today)
    except Exception as e:
        logging.error(f"Error fetching project details: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@bp.route('/project/<project_id>/actions', methods=['GET', 'POST'])
def project_actions(project_id):
    if request.method == 'POST':
        data = request.get_json()
        action_type = data.get('action_type')
        description = data.get('description')

        new_action = ProjectAction(
            project_id=project_id,
            action_type=action_type,
            description=description
        )
        db.session.add(new_action)
        db.session.commit()

        return jsonify({'success': True, 'message': '액션이 추가되었습니다.'})

    # GET 요청 시 처리 내역 반환
    actions = ProjectAction.query.filter_by(project_id=project_id).all()
    return jsonify([{
        'action_type': action.action_type,
        'action_date': action.action_date.strftime('%Y-%m-%d %H:%M'),
        'description': action.description
    } for action in actions])

@bp.route('/project/<uuid:project_id>/send-email/<email_type>', methods=['POST'])
async def send_email_api(project_id, email_type):
    """
    이메일을 발송합니다.
    """
    try:
        project = Project.query.get_or_404(project_id)
        request_data = request.get_json() or {}
        
        # 이메일 타입 포맷 변환 (URL 형식 -> enum 형식)
        email_type_enum = None
        
        # 하이픈 형식이 있는 경우 (현재 URL에서는 하이픈 형식을 사용하므로 호환성 유지)
        if '-' in email_type:
            try:
                for et in EmailType:
                    # application-complete -> application_complete와 같이 변환
                    if et.value == email_type.replace('-', '_'):
                        email_type_enum = et
                        break
                
                # 일치하는 타입이 없으면 대문자로 변환하여 시도
                if not email_type_enum:
                    email_type_enum = EmailType[email_type.upper().replace('-', '_')]
            except (KeyError, ValueError):
                return jsonify({
                    'success': False,
                    'message': '잘못된 이메일 타입입니다.',
                    'type': 'invalid_email_type'
                }), 400
        else:
            # 하이픈이 없는 경우 (예: application_complete)
            try:
                email_type_enum = EmailType(email_type)
            except ValueError:
                try:
                    email_type_enum = EmailType[email_type.upper()]
                except KeyError:
                    return jsonify({
                        'success': False,
                        'message': '잘못된 이메일 타입입니다.',
                        'type': 'invalid_email_type'
                    }), 400
        
        if not email_type_enum:
            return jsonify({
                'success': False,
                'message': '이메일 타입을 확인할 수 없습니다.',
                'type': 'invalid_email_type'
            }), 400
        
        logging.info(f"이메일 발송 요청: {project_id}, {email_type} -> {email_type_enum}")
        
        # 이메일 설정 가져오기
        if email_type_enum not in EMAIL_CONFIG:
            return jsonify({
                'success': False,
                'message': f'지원되지 않는 이메일 타입: {email_type}',
                'type': 'invalid_email_type'
            }), 400
            
        config = EMAIL_CONFIG[email_type_enum]
        
        # 상태 변경이 필요한 경우 처리
        if request_data.get('update_status') and 'target_status' in config:
            # 현재 상태가 허용된 상태인지 확인
            if 'allowed_from_statuses' in config and config['allowed_from_statuses'] and project.status not in config['allowed_from_statuses']:
                allowed_statuses = ', '.join([status.value for status in config['allowed_from_statuses']])
                return jsonify({
                    'success': False,
                    'message': f"{email_type.value} 이메일은 {allowed_statuses} 상태에서만 발송 가능합니다. 현재 상태: {project.status.value}",
                    'type': 'invalid_status'
                }), 400
            
            old_status = project.status
            project.status = config['target_status']
            
            # 상태 변경 이력 저장
            status_history = StatusHistory(
                project_id=project_id,
                previous_status=old_status,
                new_status=project.status,
                created_by=request_data.get('created_by', 'System'),
                reason=request_data.get('reason', f'{email_type} 이메일 발송에 의한 자동 상태 변경')
            )
            db.session.add(status_history)
            db.session.commit()
            logger.info(f"프로젝트 {project_id} 상태가 {project.status.value}로 업데이트되었습니다.")

        # 추가 데이터 준비
        additional_data = {}
        if request_data.get('additional_data'):
            additional_data.update(request_data['additional_data'])
            
        # 이메일 발송
        success, error_msg = await send_email(project, email_type_enum, additional_data)
        
        if success:
            return jsonify({
                'success': True,
                'message': '이메일이 성공적으로 발송되었습니다.',
                'project': {
                    'id': project.id,
                    'name': project.name,
                    'company': project.company,
                    'email': project.email,
                    'phone': project.phone,
                    'project_type': project.project_type,
                    'project_url': project.project_url,
                    'purpose': project.purpose,
                    'status': project.status.value
                }
            })
        else:
            return jsonify({
                'success': False,
                'message': f'이메일 발송 중 오류가 발생했습니다: {error_msg}',
                'type': 'email_error'
            }), 500
    except Exception as e:
        logger.error(f"이메일 발송 중 오류: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'이메일 발송 중 오류가 발생했습니다: {str(e)}',
            'type': 'server_error'
        }), 500

@bp.route('/project/<uuid:project_id>/send-email/<email_type>', methods=['GET', 'POST'])
def send_email_page(project_id, email_type):
    """
    이메일 발송 페이지를 표시합니다.
    """
    form = EmailForm()
    project = Project.query.get_or_404(project_id)
    
    try:
        # 이메일 타입 포맷 변환 (URL 형식 -> enum 형식)
        email_type_enum = None
        
        # 하이픈 형식이 있는 경우 (현재 URL에서는 하이픈 형식을 사용하므로 호환성 유지)
        if '-' in email_type:
            try:
                for et in EmailType:
                    # application-complete -> application_complete와 같이 변환
                    if et.value == email_type.replace('-', '_'):
                        email_type_enum = et
                        break
                
                # 일치하는 타입이 없으면 대문자로 변환하여 시도
                if not email_type_enum:
                    email_type_enum = EmailType[email_type.upper().replace('-', '_')]
            except (KeyError, ValueError):
                logger.error(f"Invalid email type: {email_type}")
                abort(400, f"Invalid email type: {email_type}")
        else:
            # 하이픈이 없는 경우 (예: application_complete)
            try:
                email_type_enum = EmailType(email_type)
            except ValueError:
                try:
                    email_type_enum = EmailType[email_type.upper()]
                except KeyError:
                    logger.error(f"Invalid email type: {email_type}")
                    abort(400, f"Invalid email type: {email_type}")
        
        # 이메일 설정 가져오기
        if email_type_enum not in EMAIL_CONFIG:
            logger.error(f"지원되지 않는 이메일 타입: {email_type}")
            abort(400, f"지원되지 않는 이메일 타입: {email_type}")
        
        config = EMAIL_CONFIG[email_type_enum]
        preview_url = config['template']
        
        return render_template(
            config['page_template'],
            form=form,
            project=project,
            email_type=email_type_enum,
            preview_url=preview_url
        )
            
    except Exception as e:
        logger.error(f"이메일 페이지 로드 중 오류: {str(e)}")
        flash(f'이메일 페이지 로드 중 오류가 발생했습니다: {str(e)}', 'danger')
        return redirect(url_for('main.project_detail', project_id=project_id))

@bp.route('/project/<project_id>/mail/submission-complete', methods=['GET', 'POST'])
def send_submission_complete_mail_page(project_id):
    """접수 완료 이메일 발송 페이지"""
    project = Project.query.get_or_404(project_id)
    form = EmailForm(obj=project)
    email_type = EmailType.SUBMISSION_COMPLETE
    preview_url = EMAIL_CONFIG[email_type]['template'] if email_type in EMAIL_CONFIG else None
    
    return render_template(
        EMAIL_CONFIG[email_type]['page_template'] if email_type in EMAIL_CONFIG and 'page_template' in EMAIL_CONFIG[email_type] else 'submission_complete.html',
        form=form,
        project=project,
        email_type=email_type,
        preview_url=preview_url
    )

@bp.route('/project/<project_id>/mail/application-complete', methods=['GET', 'POST'])
def send_application_complete_mail_page(project_id):
    """신청 완료 이메일 발송 페이지"""
    project = Project.query.get_or_404(project_id)
    form = EmailForm(obj=project)
    email_type = EmailType.APPLICATION_COMPLETE
    preview_url = EMAIL_CONFIG[email_type]['template'] if email_type in EMAIL_CONFIG else None
    
    return render_template(
        EMAIL_CONFIG[email_type]['page_template'] if email_type in EMAIL_CONFIG and 'page_template' in EMAIL_CONFIG[email_type] else 'application_complete.html',
        form=form, 
        project=project,
        email_type=email_type,
        preview_url=preview_url
    )

@bp.route('/project/<project_id>/mail/submission_complete', methods=['GET', 'POST'])
def send_submission_complete_mail_page_underscore(project_id):
    """접수 완료 이메일 발송 페이지 (언더스코어 버전)"""
    return send_submission_complete_mail_page(project_id)

@bp.route('/project/<project_id>/mail/application_complete', methods=['GET', 'POST'])
def send_application_complete_mail_page_underscore(project_id):
    """신청 완료 이메일 발송 페이지 (언더스코어 버전)"""
    return send_application_complete_mail_page(project_id)

@bp.route('/project/<project_id>/mail/poc_complete', methods=['GET', 'POST'])
def send_poc_complete_mail_page_underscore(project_id):
    """POC 완료 이메일 발송 페이지 (언더스코어 버전)"""
    return send_report_mail_page(project_id)

@bp.route('/project/<project_id>/mail/cancellation', methods=['GET', 'POST'])
def send_cancel_mail_page(project_id):
    """취소 이메일 발송 페이지"""
    project = Project.query.get_or_404(project_id)
    form = EmailForm(obj=project)
    email_type = EmailType.CANCELLATION
    preview_url = EMAIL_CONFIG[email_type]['template'] if email_type in EMAIL_CONFIG else None
    
    return render_template(
        'cancel_mail.html',
        form=form, 
        project=project,
        email_type=email_type,
        preview_url=preview_url
    )

@bp.route('/project/<project_id>/mail/misc', methods=['GET', 'POST'])
def send_misc_mail_page(project_id):
    """기타 안내 이메일 발송 페이지"""
    project = Project.query.get_or_404(project_id)
    form = EmailForm(obj=project)
    email_type = EmailType.MISC
    preview_url = EMAIL_CONFIG[email_type]['template'] if email_type in EMAIL_CONFIG else None
    
    return render_template(
        'misc_mail.html',
        form=form, 
        project=project,
        email_type=email_type,
        preview_url=preview_url
    )

@bp.route('/project/<project_id>/mail/delay', methods=['GET', 'POST'])
def send_delay_mail_page(project_id):
    """기간 연장 이메일 발송 페이지"""
    project = Project.query.get_or_404(project_id)
    form = EmailForm(obj=project)
    email_type = EmailType.DELAY
    preview_url = EMAIL_CONFIG[email_type]['template'] if email_type in EMAIL_CONFIG else None
    
    return render_template(
        'delay_mail.html',
        form=form, 
        project=project,
        email_type=email_type,
        preview_url=preview_url
    )

@bp.route('/project/<project_id>/mail/report', methods=['GET', 'POST'])
def send_report_mail_page(project_id):
    """보고서 이메일 발송 페이지"""
    project = Project.query.get_or_404(project_id)
    form = EmailForm(obj=project)
    email_type = EmailType.POC_COMPLETE
    preview_url = EMAIL_CONFIG[email_type]['template'] if email_type in EMAIL_CONFIG else None
    
    return render_template(
        'report_mail.html',
        form=form, 
        project=project,
        email_type=email_type,
        preview_url=preview_url
    )

@bp.route('/project/<project_id>/mail/delay', methods=['POST'])
async def send_delay_mail_api(project_id):
    """기간 연장 이메일 발송 API"""
    try:
        project = Project.query.get_or_404(project_id)
        data = request.get_json()
        
        # 새 보고서 날짜 설정
        new_date = datetime.strptime(data.get('new_date'), '%Y-%m-%d')
        
        # 프로젝트 보고서 예상 날짜 업데이트
        project.expected_report_date = new_date
        db.session.commit()
        
        # 이메일 발송 처리
        additional_data = {
            '기존날짜': project.created_at.strftime('%Y-%m-%d'),
            '연장날짜': new_date.strftime('%Y-%m-%d')
        }
        
        success, error = await send_email(
            project=project,
            email_type=EmailType.DELAY,
            additional_data=additional_data
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': '기간 연장 안내 이메일이 발송되었습니다.',
                'project': {
                    'id': project.id,
                    'expected_report_date': project.expected_report_date.strftime('%Y-%m-%d')
                }
            })
        else:
            return jsonify({
                'success': False,
                'message': f'이메일 발송 중 오류가 발생했습니다: {error}',
                'type': 'email_error'
            }), 500
        
    except Exception as e:
        logger.error(f"기간 연장 이메일 발송 중 오류: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'이메일 발송 중 오류가 발생했습니다: {str(e)}',
            'type': 'server_error'
        }), 500

@bp.route('/project/<project_id>/mail/complete')
def send_complete_mail_page(project_id):
    """완료 이메일 발송 페이지"""
    project = Project.query.get_or_404(project_id)
    form = EmailForm(obj=project)
    email_type = EmailType.POC_COMPLETE
    return render_template(
        EMAIL_CONFIG[email_type]['page_template'],
        form=form, 
        project=project,
        email_type=email_type,
        preview_url=EMAIL_CONFIG[email_type]['template']
    )

@bp.route('/project/<project_id>/status', methods=['POST'])
async def update_project_status(project_id):
    try:
        data = request.get_json()
        project = Project.query.get_or_404(project_id)
        
        # 원본 상태 저장
        old_status = project.status
        
        # 상태 문자열 처리 (소문자로 받은 경우 매핑)
        status_str = data['status'].lower()
        
        # 상태값 매핑 처리
        status_map = {
            'cancelled': ProjectStatus.CANCELLED,
            'application_complete': ProjectStatus.APPLICATION_COMPLETE,
            'reception_complete': ProjectStatus.RECEPTION_COMPLETE, 
            'poc_in_progress': ProjectStatus.POC_IN_PROGRESS,
            'delayed': ProjectStatus.DELAYED,
            'poc_complete': ProjectStatus.POC_COMPLETE,
            # 간단한 표기에 대한 매핑 추가
            'cancel': ProjectStatus.CANCELLED,
            'complete': ProjectStatus.POC_COMPLETE,
            'completed': ProjectStatus.POC_COMPLETE,
            'delay': ProjectStatus.DELAYED
        }
        
        if status_str not in status_map:
            return jsonify({'success': False, 'message': f'알 수 없는 상태값입니다: {status_str}'}), 400
            
        new_status = status_map[status_str]
        
        # 이미 같은 상태인 경우 처리 생략
        if project.status == new_status:
            return jsonify({
                'success': True,
                'message': f'프로젝트가 이미 {new_status.value} 상태입니다.'
            })
        
        # 프로젝트 취소 처리인 경우 이메일 전송
        if new_status == ProjectStatus.CANCELLED:
            logging.info(f"취소 처리 시작: {project_id}")
            # 취소 이메일 발송
            success, error_message = await send_mail(
                project.email,
                f"RTM AI POC 취소 안내 - {project.company}",
                render_template(
                    'email/online-poc-email-cancel.html',
                    프로젝트ID=project.id,
                    이름=project.name,
                    회사명=project.company,
                    유형=project.project_type,
                    취소사유=data.get('reason', '사유 없음'),
                    프로젝트관리페이지=project.project_url
                )
            )
            
            # 이메일 로그 추가
            email_log = EmailHistory(
                project_id=project.id,
                email_type=EmailType.CANCELLATION,
                subject=f"RTM AI POC 취소 안내 - {project.company}",
                recipient=project.email,
                status='success' if success else 'failed',
                error_message=error_message if not success else None
            )
            db.session.add(email_log)
            
            # 이메일 발송 실패 시 상태 변경 안함
            if not success:
                db.session.commit()  # 이메일 로그만 저장
                return jsonify({
                    'success': False, 
                    'message': f'이메일 발송에 실패했습니다: {error_message}. 프로젝트 상태가 변경되지 않았습니다.'
                }), 500
            
            logging.info(f"취소 이메일 발송 완료: {project_id}")
        
        # 상태 업데이트
        project.status = new_status
        logging.info(f"프로젝트 상태 변경: {old_status.value} -> {new_status.value}")
        
        # 취소 또는 완료 처리 시 완료일 기록
        if new_status in [ProjectStatus.CANCELLED, ProjectStatus.POC_COMPLETE]:
            project.completed_at = datetime.utcnow()
            if new_status == ProjectStatus.CANCELLED:
                project.cancel_reason = data.get('reason')
        
        # 상태 변경 이력 저장
        status_history = StatusHistory(
            project_id=project_id,
            previous_status=old_status,
            new_status=new_status,
            created_by=request.headers.get('X-User-Name', 'System'),
            reason=data.get('reason')
        )
        db.session.add(status_history)
        db.session.commit()
        logging.info(f"프로젝트 상태 변경 완료: {project_id}")
        
        return jsonify({
            'success': True, 
            'message': '이메일이 성공적으로 발송되었으며, 상태가 변경되었습니다.' if new_status == ProjectStatus.CANCELLED else '상태가 성공적으로 변경되었습니다.'
        })
        
    except KeyError as e:
        logging.error(f"상태 변경 중 KeyError: {str(e)}")
        return jsonify({'success': False, 'message': f'잘못된 상태값입니다: {str(e)}'})
    except Exception as e:
        db.session.rollback()
        logging.error(f"상태 변경 중 오류 발생: {str(e)}")
        return jsonify({'success': False, 'message': f'오류가 발생했습니다: {str(e)}'})

@bp.route('/project/<project_id>/report/download')
def download_report(project_id):
    try:
        project = Project.query.get_or_404(project_id)
        
        if not project.report_file:
            return jsonify({'success': False, 'message': '리포트 파일이 없습니다.'})
        
        file_path = os.path.join('uploads', 'reports', project.report_file)
        
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'message': '리포트 파일을 찾을 수 없습니다.'})
        
        return send_file(
            file_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'POC_Report_{project.company}_{get_korea_time().strftime("%Y%m%d")}.pdf'
        )
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/project/<project_id>/validate-status', methods=['POST'])
def validate_project_status(project_id):
    """프로젝트 상태 검증 API"""
    try:
        project = Project.query.get_or_404(project_id)
        
        # 요청에서 예상하는 상태 가져오기
        data = request.get_json() or {}
        expected_status = data.get('expected_status')
        email_type_str = data.get('email_type')
        
        # 이메일 타입이 지정된 경우, 해당 이메일의 허용된 상태 목록 확인
        if email_type_str:
            email_type = None
            
            # 이메일 타입 문자열을 EmailType으로 변환
            try:
                # 하이픈이 있는 경우 언더스코어로 변환하여 시도
                if '-' in email_type_str:
                    email_type_key = email_type_str.upper().replace('-', '_')
                    email_type = EmailType[email_type_key]
                else:
                    # 언더스코어 형식 그대로 시도
                    email_type = EmailType(email_type_str)
            except (ValueError, KeyError):
                try:
                    # 대문자로 변환하여 시도
                    email_type = EmailType[email_type_str.upper()]
                except KeyError:
                    return jsonify({
                        'success': False,
                        'message': f'잘못된 이메일 타입: {email_type_str}'
                    }), 400
            
            if email_type and email_type in EMAIL_CONFIG:
                config = EMAIL_CONFIG[email_type]
                
                # 허용된 상태 목록이 있는 경우 검증
                if 'allowed_from_statuses' in config and config['allowed_from_statuses']:
                    if project.status not in config['allowed_from_statuses']:
                        allowed_statuses = ', '.join([status.value for status in config['allowed_from_statuses']])
                        return jsonify({
                            'success': True,
                            'is_valid': False,
                            'message': f"{email_type.value} 이메일은 {allowed_statuses} 상태에서만 발송 가능합니다. 현재 상태: {project.status.value}",
                            'project': {
                                'id': project.id,
                                'status': project.status.value
                            }
                        })
                    
                    # 허용된 상태이면 유효
                    return jsonify({
                        'success': True,
                        'is_valid': True,
                        'message': f"{email_type.value} 이메일은 현재 상태({project.status.value})에서 발송 가능합니다.",
                        'project': {
                            'id': project.id,
                            'status': project.status.value,
                            'name': project.name,
                            'company': project.company,
                            'email': project.email,
                            'phone': project.phone,
                            'project_type': project.project_type,
                            'project_url': project.project_url,
                            'purpose': project.purpose
                        }
                    })
            
        # expected_status로 직접 검증하는 경우 (이전 방식 호환성)
        is_valid = True
        message = "상태가 유효합니다."
        
        # expected_status가 지정되었을 때만 검증
        if expected_status and project.status.value != expected_status:
            # SUBMISSION_COMPLETE 이메일을 위한 특별 검증 (이전 방식 호환성)
            if expected_status == 'reception_complete' and project.status.value == 'application_complete':
                is_valid = True
                message = "APPLICATION_COMPLETE 상태에서 SUBMISSION_COMPLETE 이메일을 보낼 수 있습니다."
            else:
                is_valid = False
                message = f"예상 상태({expected_status})와 현재 상태({project.status.value})가 일치하지 않습니다."
        
        # 프로젝트 정보 반환
        project_info = {
            'id': project.id,
            'status': project.status.value,
            'name': project.name,
            'company': project.company,
            'email': project.email,
            'phone': project.phone,
            'project_type': project.project_type,
            'project_url': project.project_url,
            'purpose': project.purpose
        }
        
        return jsonify({
            'success': True,
            'is_valid': is_valid,
            'message': message,
            'project': project_info
        })

    except Exception as e:
        logger.error(f"프로젝트 상태 검증 중 오류: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'프로젝트 상태 검증 중 오류가 발생했습니다: {str(e)}'
        }), 500

@bp.route('/preview/delay', methods=['POST'])
def preview_delay():
    """지연 안내 이메일 미리보기"""
    try:
        data = request.get_json() or {}
        
        # 필드 매핑 - 기존 템플릿 형식으로 변환
        template_data = {
            '프로젝트ID': data.get('project_id', ''),
            '이름': data.get('name', ''),
            '회사명': data.get('company', ''),
            '유형': data.get('project_type', ''),
            '기존예정일': data.get('current_date', ''),
            '변경예정일': data.get('new_date', ''),
            '지연일수': calculate_days_difference(data.get('current_date', ''), data.get('new_date', '')),
            '변경사유': data.get('reason', ''),
            '프로젝트관리페이지': data.get('project_url', ''),
        }
        
        html = render_template(
            'email/online-poc-email-delay.html',
            **template_data
        )
        return html
    except Exception as e:
        logger.error(f"지연 이메일 미리보기 오류: {str(e)}")
        return "<div class='alert alert-danger'>이메일 미리보기를 생성하는 중 오류가 발생했습니다.</div>"

@bp.route('/preview/cancellation', methods=['POST'])
def preview_cancellation():
    """취소 안내 이메일 미리보기"""
    try:
        data = request.get_json() or {}
        html = render_template(
            'email_templates/cancellation.html',
            name=data.get('name', ''),
            company=data.get('company', ''),
            project_type=data.get('project_type', ''),
            project_id=data.get('project_id', ''),
            cancel_reason=data.get('cancel_reason', '')
        )
        return html
    except Exception as e:
        logger.error(f"취소 이메일 미리보기 오류: {str(e)}")
        return "<div class='alert alert-danger'>이메일 미리보기를 생성하는 중 오류가 발생했습니다.</div>"

@bp.route('/preview/poc_complete', methods=['POST'])
def preview_poc_complete():
    """POC 완료 보고서 이메일 미리보기"""
    try:
        # FormData로 전송된 파일과 데이터 처리
        data = {}
        if request.content_type and 'multipart/form-data' in request.content_type:
            # 파일과 다른 폼 데이터 처리
            data = request.form.to_dict()
            if 'report_file' in request.files:
                file = request.files['report_file']
                if file and file.filename:
                    data['report_name'] = file.filename
        else:
            # JSON 요청인 경우
            data = request.get_json() or {}
        
        # 필드 매핑 - 기존 템플릿 형식으로 변환
        template_data = {
            'name': data.get('name', ''),
            'company': data.get('company', ''),
            'project_type': data.get('project_type', ''),
            'project_id': data.get('project_id', ''),
            '접수시각': data.get('submission_time', ''),
            '완료시각': data.get('completion_date', get_korea_time().strftime('%Y-%m-%d')),
            '프로젝트관리페이지': data.get('project_url', ''),
            '보고서': data.get('report_name', ''),
            '코멘트': data.get('comment', ''),
            '로고': LOGO_BASE64,
        }
            
        html = render_template(
            'email/online-poc-email-report.html',
            **template_data
        )
        return html
    except Exception as e:
        logger.error(f"POC 완료 이메일 미리보기 오류: {str(e)}")
        return "<div class='alert alert-danger'>이메일 미리보기를 생성하는 중 오류가 발생했습니다.</div>"

@bp.route('/preview/misc', methods=['POST'])
def preview_misc():
    """기타 안내 이메일 미리보기"""
    try:
        # FormData로 전송된 파일과 데이터 처리
        data = {}
        if request.content_type and 'multipart/form-data' in request.content_type:
            # 파일과 다른 폼 데이터 처리
            data = request.form.to_dict()
            if 'attachment' in request.files:
                file = request.files['attachment']
                if file and file.filename:
                    data['attachment_filename'] = file.filename
        else:
            # JSON 요청인 경우
            data = request.get_json() or {}
        
        html = render_template(
            'email_templates/misc.html',
            name=data.get('name', ''),
            company=data.get('company', ''),
            project_type=data.get('project_type', ''),
            project_id=data.get('project_id', ''),
            email_subject=data.get('email_subject', ''),
            email_content=data.get('email_content', ''),
            attachment_filename=data.get('attachment_filename', '')
        )
        return html
    except Exception as e:
        logger.error(f"기타 안내 이메일 미리보기 오류: {str(e)}")
        return "<div class='alert alert-danger'>이메일 미리보기를 생성하는 중 오류가 발생했습니다.</div>"

@bp.route('/send-with-file', methods=['POST'])
async def send_with_file():
    """파일 첨부 이메일 발송"""
    try:
        # X-Source-Page 헤더 확인 (어떤 페이지에서 요청했는지)
        source_page = request.headers.get('X-Source-Page')
        logger.info(f"Send-with-file 요청: Source-Page={source_page}")
        
        # FormData에서 데이터 및 파일 추출
        data = request.form.to_dict()
        project_id = data.get('project_id')
        email_type = data.get('email_type')
        
        if not project_id or not email_type:
            return jsonify({
                'success': False,
                'message': '필수 정보가 누락되었습니다 (project_id 또는 email_type).'
            }), 400
        
        # 이메일 타입 확인
        try:
            email_type_enum = EmailType(email_type)
        except ValueError:
            return jsonify({
                'success': False,
                'message': f'지원되지 않는 이메일 타입: {email_type}'
            }), 400
        
        # 프로젝트 조회
        project = Project.query.get(project_id)
        if not project:
            return jsonify({
                'success': False,
                'message': f'프로젝트를 찾을 수 없습니다: {project_id}'
            }), 404
        
        # 파일 처리
        additional_data = {}
        
        if email_type_enum == EmailType.POC_COMPLETE:
            # POC 완료 보고서 처리
            if 'report_file' in request.files and request.files['report_file'].filename:
                file = request.files['report_file']
                # 파일 저장 처리 (저장 경로는 프로젝트에 맞게 조정)
                filename = secure_filename(f"{project_id}_{file.filename}")
                file_path = os.path.join('uploads', 'reports', filename)
                
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                file.save(file_path)
                
                # 프로젝트에 보고서 파일 경로 저장
                project.report_file = file_path
                
                # 추가 데이터 설정
                additional_data['report_filename'] = file.filename
                additional_data['report_summary'] = data.get('report_summary', '')
                additional_data['completion_date'] = data.get('completion_date', '')
            
            # 상태 업데이트 (POC 완료)
            old_status = project.status
            project.status = ProjectStatus.POC_COMPLETE
            
            # 상태 이력 저장
            status_history = StatusHistory(
                project_id=project_id,
                previous_status=old_status,
                new_status=project.status,
                created_by=data.get('created_by', 'System'),
                reason=f'POC 완료 보고서 제출'
            )
            db.session.add(status_history)
            
        elif email_type_enum == EmailType.MISC:
            # 기타 안내 이메일 처리
            if 'attachment' in request.files and request.files['attachment'].filename:
                file = request.files['attachment']
                # 파일 저장 처리
                filename = secure_filename(f"{project_id}_{file.filename}")
                file_path = os.path.join('uploads', 'attachments', filename)
                
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                file.save(file_path)
                
                # 추가 데이터 설정
                additional_data['attachment_filename'] = file.filename
            
            # 제목 및 내용 추가
            additional_data['email_subject'] = data.get('email_subject', '')
            additional_data['email_content'] = data.get('email_content', '')
            
        # DB 저장
        db.session.commit()
        
        # 이메일 발송
        success, error_msg = await send_email(project, email_type_enum, additional_data)
        
        if success:
            return jsonify({
                'success': True,
                'message': '이메일이 성공적으로 전송되었습니다.'
            })
        else:
            return jsonify({
                'success': False,
                'message': f'이메일 발송 중 오류가 발생했습니다: {error_msg}'
            }), 500
            
    except Exception as e:
        logger.error(f"파일 첨부 이메일 발송 중 오류: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'이메일 발송 중 오류가 발생했습니다: {str(e)}'
        }), 500

@bp.route('/create-email-templates')
def create_email_templates():
    """이메일 템플릿 파일 생성 (개발용)"""
    try:
        templates_dir = os.path.join('app', 'templates', 'email_templates')
        os.makedirs(templates_dir, exist_ok=True)
        
        # 취소 안내 템플릿
        cancellation_template = """
<!DOCTYPE html>
<html>
<head>
    <title>RTM AI POC 취소 안내</title>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { text-align: center; margin-bottom: 30px; }
        .content { margin-bottom: 30px; }
        .footer { font-size: 12px; color: #777; text-align: center; margin-top: 30px; }
        .highlight { color: #ec6707; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>RTM AI POC 취소 안내</h2>
        </div>
        
        <div class="content">
            <p>안녕하세요, <strong>{{ company }}</strong>의 <strong>{{ name }}</strong>님.</p>
            
            <p>귀하께서 요청하신 <span class="highlight">{{ project_type }}</span> 프로젝트(ID: {{ project_id }})가 다음의 이유로 취소되었음을 알려드립니다:</p>
            
            <div style="background-color: #f5f5f5; padding: 15px; border-left: 4px solid #ec6707; margin: 20px 0;">
                <p><strong>취소 사유:</strong></p>
                <p>{{ cancel_reason }}</p>
            </div>
            
            <p>본 취소와 관련하여 추가적인 문의사항이 있으시면 언제든지 연락주시기 바랍니다.</p>
            
            <p>감사합니다.</p>
            <p>RTM AI 팀 드림</p>
        </div>
        
        <div class="footer">
            <p>본 이메일은 자동발송 메일입니다. 문의사항은 담당자에게 연락 바랍니다.</p>
            <p>&copy; 2025 RTM Inc. All Rights Reserved.</p>
        </div>
    </div>
</body>
</html>
"""
        
        # 지연 안내 템플릿
        delay_template = """
<!DOCTYPE html>
<html>
<head>
    <title>RTM AI POC 지연 안내</title>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { text-align: center; margin-bottom: 30px; }
        .content { margin-bottom: 30px; }
        .footer { font-size: 12px; color: #777; text-align: center; margin-top: 30px; }
        .highlight { color: #ec6707; font-weight: bold; }
        .info-box { background-color: #f5f5f5; padding: 15px; border-left: 4px solid #ec6707; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>RTM AI POC 지연 안내</h2>
        </div>
        
        <div class="content">
            <p>안녕하세요, <strong>{{ company }}</strong>의 <strong>{{ name }}</strong>님.</p>
            
            <p>귀하께서 요청하신 <span class="highlight">{{ project_type }}</span> 프로젝트(ID: {{ project_id }})의 완료 일정이 변경되었음을 알려드립니다.</p>
            
            <div class="info-box">
                <p><strong>완료 예정일 변경 안내:</strong></p>
                <p>당초 예정일: {{ expected_date|default('해당 없음') }}</p>
                <p>변경 예정일: {{ delayed_date|default('미정') }}</p>
                <p><strong>지연 사유:</strong></p>
                <p>{{ delay_reason }}</p>
            </div>
            
            <p>일정 변경으로 인해 불편을 드려 죄송합니다. 변경된 일정에 맞춰 최상의 결과물을 제공해 드리기 위해 최선을 다하겠습니다.</p>
            
            <p>추가적인 문의사항이 있으시면 언제든지 연락주시기 바랍니다.</p>
            
            <p>감사합니다.</p>
            <p>RTM AI 팀 드림</p>
        </div>
        
        <div class="footer">
            <p>본 이메일은 자동발송 메일입니다. 문의사항은 담당자에게 연락 바랍니다.</p>
            <p>&copy; 2025 RTM Inc. All Rights Reserved.</p>
        </div>
    </div>
</body>
</html>
"""

        # POC 완료 보고서 템플릿
        poc_complete_template = """
<!DOCTYPE html>
<html>
<head>
    <title>RTM AI POC 완료 보고서</title>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { text-align: center; margin-bottom: 30px; }
        .content { margin-bottom: 30px; }
        .footer { font-size: 12px; color: #777; text-align: center; margin-top: 30px; }
        .highlight { color: #28a745; font-weight: bold; }
        .info-box { background-color: #f5f5f5; padding: 15px; border-left: 4px solid #28a745; margin: 20px 0; }
        .attachment { background-color: #e9f7ef; padding: 15px; border-radius: 5px; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>RTM AI POC 완료 보고서</h2>
        </div>
        
        <div class="content">
            <p>안녕하세요, <strong>{{ company }}</strong>의 <strong>{{ name }}</strong>님.</p>
            
            <p>귀하께서 요청하신 <span class="highlight">{{ project_type }}</span> 프로젝트(ID: {{ project_id }})가 성공적으로 완료되었음을 알려드립니다.</p>
            
            <div class="info-box">
                <p><strong>완료일:</strong> {{ completion_date|default('오늘') }}</p>
                <p><strong>분석 결과 요약:</strong></p>
                <p>{{ report_summary }}</p>
            </div>
            
            {% if report_filename %}
            <div class="attachment">
                <p><strong>첨부 파일:</strong> {{ report_filename }}</p>
                <p>상세한 분석 결과는 첨부된 보고서를 참고하시기 바랍니다.</p>
            </div>
            {% endif %}
            
            <p>본 프로젝트에 관한 문의사항이나 추가 요청사항이 있으시면 언제든지 연락주시기 바랍니다.</p>
            
            <p>감사합니다.</p>
            <p>RTM AI 팀 드림</p>
        </div>
        
        <div class="footer">
            <p>본 이메일은 자동발송 메일입니다. 문의사항은 담당자에게 연락 바랍니다.</p>
            <p>&copy; 2025 RTM Inc. All Rights Reserved.</p>
        </div>
    </div>
</body>
</html>
"""

        # 기타 안내 이메일 템플릿
        misc_template = """
<!DOCTYPE html>
<html>
<head>
    <title>{{ email_subject|default('RTM AI POC 안내') }}</title>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { text-align: center; margin-bottom: 30px; }
        .content { margin-bottom: 30px; }
        .footer { font-size: 12px; color: #777; text-align: center; margin-top: 30px; }
        .highlight { color: #ec6707; font-weight: bold; }
        .attachment { background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>{{ email_subject|default('RTM AI POC 안내') }}</h2>
        </div>
        
        <div class="content">
            <p>안녕하세요, <strong>{{ company }}</strong>의 <strong>{{ name }}</strong>님.</p>
            
            <p>귀하께서 요청하신 <span class="highlight">{{ project_type }}</span> 프로젝트(ID: {{ project_id }})와 관련하여 아래와 같이 안내드립니다.</p>
            
            <div style="margin: 20px 0;">
                {{ email_content|safe }}
            </div>
            
            {% if attachment_filename %}
            <div class="attachment">
                <p><strong>첨부 파일:</strong> {{ attachment_filename }}</p>
                <p>자세한 내용은 첨부파일을 참고하시기 바랍니다.</p>
            </div>
            {% endif %}
            
            <p>추가적인 문의사항이 있으시면 언제든지 연락주시기 바랍니다.</p>
            
            <p>감사합니다.</p>
            <p>RTM AI 팀 드림</p>
        </div>
        
        <div class="footer">
            <p>본 이메일은 자동발송 메일입니다. 문의사항은 담당자에게 연락 바랍니다.</p>
            <p>&copy; 2025 RTM Inc. All Rights Reserved.</p>
        </div>
    </div>
</body>
</html>
"""

        # 각 템플릿 파일 저장
        template_files = {
            'cancellation.html': cancellation_template,
            'delay.html': delay_template,
            'poc_complete.html': poc_complete_template,
            'misc.html': misc_template
        }
        
        for filename, content in template_files.items():
            filepath = os.path.join(templates_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
        
        return jsonify({
            'success': True,
            'message': '이메일 템플릿이 성공적으로 생성되었습니다.',
            'templates': list(template_files.keys())
        })
    except Exception as e:
        logger.error(f"이메일 템플릿 생성 중 오류: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'이메일 템플릿 생성 중 오류가 발생했습니다: {str(e)}'
        }), 500

@bp.route('/check-project-exists/<project_id>', methods=['GET'])
def check_project_exists(project_id):
    """프로젝트 존재 여부 및 이메일 발송 여부 확인"""
    try:
        project = Project.query.get(project_id)
        
        if not project:
            return jsonify({
                'exists': False,
                'email_sent': False
            }), 200
        
        # 프로젝트가 존재하면 application_complete 이메일이 발송되었는지 확인
        application_complete_emails = EmailHistory.query.filter_by(
            project_id=project_id, 
            email_type=EmailType.APPLICATION_COMPLETE,
            status='success'
        ).all()
        
        return jsonify({
            'exists': True,
            'email_sent': len(application_complete_emails) > 0,
            'status': project.status.value
        }), 200
        
    except Exception as e:
        logger.error(f"프로젝트 검증 중 오류: {str(e)}")
        return jsonify({
            'exists': False,
            'email_sent': False,
            'error': str(e)
        }), 500

@bp.route('/create-email-log', methods=['POST'])
def create_email_log():
    """이메일 발송 로그 생성"""
    try:
        data = request.get_json()
        required_fields = ['project_id', 'email_type', 'subject', 'recipient', 'status']
        
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'필수 필드 누락: {field}'
                }), 400
        
        # 이메일 타입 확인
        try:
            email_type_enum = EmailType(data['email_type'])
        except ValueError:
            try:
                email_type_enum = EmailType[data['email_type'].upper()]
            except KeyError:
                return jsonify({
                    'success': False,
                    'message': f'유효하지 않은 이메일 타입: {data["email_type"]}'
                }), 400
        
        # 이메일 로그 생성
        email_log = EmailHistory(
            project_id=data['project_id'],
            email_type=email_type_enum,
            subject=data['subject'],
            recipient=data['recipient'],
            status=data['status'],
            error_message=data.get('error_message', ''),
            sent_at=utcnow_to_korea()
        )
        
        db.session.add(email_log)
        status_updated = False
        
        # 성공적인 이메일 발송인 경우에만 상태 업데이트
        if data['status'] == 'success':
            project = Project.query.get(data['project_id'])
            if project:
                # 이미 해당 타입의 이메일이 성공적으로 발송되었는지 확인
                previous_successful_email = EmailHistory.query.filter_by(
                    project_id=data['project_id'], 
                    email_type=email_type_enum,
                    status='success'
                ).first()
                
                # 이전에 성공적으로 보낸 이메일이 없는 경우에만 상태 업데이트
                if not previous_successful_email or email_type_enum in [EmailType.DELAY, EmailType.MISC]:
                    # 현재 프로젝트 상태에서 이메일 타입이 허용되는지 확인
                    if is_email_allowed_for_current_status(project.status, email_type_enum):
                        old_status = project.status
                        new_status = None
                        
                        # 이메일 타입에 따른 상태 업데이트
                        if email_type_enum == EmailType.SUBMISSION_COMPLETE:
                            new_status = ProjectStatus.RECEPTION_COMPLETE
                            reason = '제출 완료 이메일 발송으로 인한 자동 상태 변경'
                        elif email_type_enum == EmailType.APPLICATION_COMPLETE and project.status != ProjectStatus.APPLICATION_COMPLETE:
                            new_status = ProjectStatus.APPLICATION_COMPLETE
                            reason = '신청 완료 이메일 발송으로 인한 자동 상태 변경'
                        elif email_type_enum == EmailType.POC_COMPLETE:
                            new_status = ProjectStatus.POC_COMPLETE
                            reason = 'POC 완료 이메일 발송으로 인한 자동 상태 변경'
                        elif email_type_enum == EmailType.CANCELLATION:
                            new_status = ProjectStatus.CANCELLED
                            reason = '취소 이메일 발송으로 인한 자동 상태 변경'
                        elif email_type_enum == EmailType.DELAY and project.status == ProjectStatus.POC_IN_PROGRESS:
                            new_status = ProjectStatus.DELAYED
                            reason = '지연 이메일 발송으로 인한 자동 상태 변경'
                        
                        # 상태 변경이 필요한 경우
                        if new_status and old_status != new_status:
                            project.status = new_status
                            status_updated = True
                            
                            # 상태 변경 이력 추가
                            status_history = StatusHistory(
                                project_id=data['project_id'],
                                previous_status=old_status,
                                new_status=new_status,
                                created_by='System',
                                reason=reason
                            )
                            db.session.add(status_history)
                            logger.info(f"프로젝트 {data['project_id']} 상태가 {old_status.value}에서 {new_status.value}로 업데이트되었습니다.")
                        else:
                            logger.info(f"프로젝트 {data['project_id']}의 상태 변경이 필요하지 않습니다. 현재 상태: {project.status.value}")
                    else:
                        logger.warning(f"현재 프로젝트 상태({project.status.value})에서 이메일 타입({email_type_enum.value})이 허용되지 않습니다.")
                else:
                    logger.info(f"이미 {email_type_enum.value} 타입의 이메일이 성공적으로 발송되어 있습니다. 상태 변경 없음.")
        else:
            # 이메일 발송 실패 시 로그만 추가하고 상태 변경 안함
            logger.warning(f"이메일 발송 실패로 프로젝트 {data['project_id']} 상태 변경 없음: {data.get('error_message', '')}")
        
        try:
            db.session.commit()
            return jsonify({
                'success': True,
                'message': '이메일 발송 로그가 성공적으로 생성되었습니다.',
                'status_updated': status_updated
            }), 200
        except Exception as e:
            db.session.rollback()
            logger.error(f"이메일 로그 저장 중 DB 오류: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'이메일 로그 저장 중 DB 오류가 발생했습니다: {str(e)}'
            }), 500
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"이메일 로그 생성 중 오류: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'이메일 로그 생성 중 오류가 발생했습니다: {str(e)}'
        }), 500

def prepare_email_content(project, email_type, additional_data=None):
    """이메일 내용을 준비합니다"""
    try:
        logger.info(f"이메일 콘텐츠 준비: {email_type.value}")
        
        # 이메일 타입에 따라 템플릿 및 제목 설정
        if email_type == EmailType.APPLICATION_COMPLETE:
            template_path = "email/online-poc-email-welcome.html"
            subject = f"[RTM AI] {project.company} POC 신청이 접수되었습니다"
        elif email_type == EmailType.SUBMISSION_COMPLETE:
            template_path = "email/online-poc-email-complete.html"
            subject = f"[RTM AI] {project.company} POC 제출이 완료되었습니다"
        elif email_type == EmailType.POC_COMPLETE:
            template_path = "email/online-poc-email-report.html"
            subject = f"[RTM AI] {project.company} POC 결과 보고서가 완료되었습니다"
        elif email_type == EmailType.DELAY:
            template_path = "email/online-poc-email-delay.html"
            subject = f"[RTM AI] {project.company} POC 진행 지연 안내"
        elif email_type == EmailType.CANCELLATION:
            template_path = "email/online-poc-email-cancellation.html"
            subject = f"[RTM AI] {project.company} POC 취소 안내"
        elif email_type == EmailType.MISC:
            template_path = "email/online-poc-email-misc.html"
            subject = f"[RTM AI] {project.company} POC 관련 안내"
        else:
            logger.error(f"지원되지 않는 이메일 타입: {email_type.value}")
            return None, None
        
        # 데이터 준비
        email_data = {
            "name": project.name,
            "company": project.company,
            "email": project.email,
            "phone": project.phone,
            "project_id": project.id,
            "project_type": project.project_type,
            "project_url": project.project_url,
            "purpose": project.purpose or "",
            "submission_time": project.created_at.strftime('%Y년 %m월 %d일 %H시 %M분') if project.created_at else get_korea_time().strftime('%Y년 %m월 %d일 %H시 %M분')
        }
        
        # 추가 데이터가 있으면 병합
        if additional_data:
            email_data.update(additional_data)
        
        # 템플릿 렌더링
        try:
            html_content = render_template(template_path, **email_data)
            logger.info(f"이메일 템플릿 렌더링 성공: {template_path}")
            return subject, html_content
        except Exception as e:
            logger.error(f"이메일 템플릿 렌더링 오류: {str(e)}")
            
            # 기본 템플릿 생성 시도
            try:
                # 기본 템플릿 경로
                default_template = "email/default_template.html"
                html_content = render_template(default_template, **email_data)
                logger.info(f"기본 이메일 템플릿 사용: {default_template}")
                return subject, html_content
            except Exception as e2:
                logger.error(f"기본 이메일 템플릿 렌더링 오류: {str(e2)}")
                
                # 마지막 수단으로 간단한 HTML 생성
                basic_html = f"""
                <html>
                <head>
                    <style>
                        body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                        .header {{ text-align: center; margin-bottom: 20px; }}
                        .footer {{ text-align: center; margin-top: 30px; font-size: 12px; color: #777; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h2>{subject}</h2>
                        </div>
                        <p>안녕하세요, {project.name}님,</p>
                        <p>{project.company}의 RTM AI POC 프로젝트 ({project.project_type}) 정보입니다.</p>
                        <p>프로젝트 ID: {project.id}</p>
                        <p>문의사항이 있으시면 onlinepoc@rtm.ai로 연락해주세요.</p>
                        <div class="footer">
                            <p>본 메일은 자동 발송되었습니다.</p>
                            <p>&copy; RTM AI</p>
                        </div>
                    </div>
                </body>
                </html>
                """
                logger.info("간단한 HTML 이메일 생성")
                return subject, basic_html
    
    except Exception as e:
        logger.error(f"이메일 콘텐츠 준비 중 오류: {str(e)}")
        return None, None

async def send_mail(to_email, subject, html_content, cc_list=None):
    """이메일을 발송합니다."""
    try:
        # 메일 활성화 여부 확인 (변수가 없으면 기본값으로 True 설정)
        mail_enabled = current_app.config.get('MAIL_ENABLED', True)
        if not mail_enabled:
            logger.warning("이메일 발송이 비활성화되어 있습니다.")
            return True, "이메일 발송 비활성화 (테스트 모드)"
        
        from flask_mail import Message
        from app import mail
        
        # 발신자 이메일 설정
        sender_email = current_app.config.get('MAIL_DEFAULT_SENDER')
        if not sender_email:
            logger.error("MAIL_DEFAULT_SENDER 설정이 없습니다.")
            return False, "발신자 이메일이 설정되지 않았습니다. 환경변수 SMTP_FROM을 확인하세요."
        
        # 이메일 메시지 생성
        message = Message(
            subject=subject,
            recipients=[to_email],
            html=html_content,
            sender=sender_email
        )
        
        # CC 추가 (있는 경우)
        if cc_list:
            message.cc = cc_list
            
        # 이메일 전송
        mail.send(message)
        
        logger.info(f"이메일 발송 성공: {to_email}, 제목: {subject}")
        return True, None
        
    except Exception as e:
        logger.error(f"이메일 발송 실패: {str(e)}")
        return False, str(e)

def is_email_allowed_for_current_status(current_status, email_type):
    """
    현재 프로젝트 상태에서 특정 이메일 타입의 발송이 허용되는지 확인
    """
    # 상태별 허용되는 이메일 타입 매핑
    allowed_email_types = {
        ProjectStatus.APPLICATION_SUBMITTED: [EmailType.APPLICATION_COMPLETE],
        ProjectStatus.APPLICATION_COMPLETE: [EmailType.SUBMISSION_COMPLETE],
        ProjectStatus.RECEPTION_COMPLETE: [EmailType.POC_IN_PROGRESS],
        ProjectStatus.POC_IN_PROGRESS: [EmailType.POC_COMPLETE, EmailType.DELAY, EmailType.CANCELLATION],
        ProjectStatus.DELAYED: [EmailType.POC_COMPLETE, EmailType.CANCELLATION],
        # 최종 상태들은 이메일 발송을 허용하지 않음
        ProjectStatus.POC_COMPLETE: [EmailType.MISC],
        ProjectStatus.CANCELLED: [EmailType.MISC],
    }
    
    # 기본적으로 모든 상태에서 MISC 이메일 허용
    for status in allowed_email_types:
        if EmailType.MISC not in allowed_email_types[status]:
            allowed_email_types[status].append(EmailType.MISC)
    
    # 취소는 대부분의 상태에서 허용
    for status in [ProjectStatus.APPLICATION_SUBMITTED, ProjectStatus.APPLICATION_COMPLETE, 
                  ProjectStatus.RECEPTION_COMPLETE, ProjectStatus.POC_IN_PROGRESS]:
        if EmailType.CANCELLATION not in allowed_email_types[status]:
            allowed_email_types[status].append(EmailType.CANCELLATION)
    
    # 현재 상태에 대한 허용 이메일 타입 목록 가져오기
    current_allowed_types = allowed_email_types.get(current_status, [])
    
    return email_type in current_allowed_types

@bp.route('/project/<project_id>/delete', methods=['POST'])
def delete_project(project_id):
    """
    프로젝트를 영구적으로 삭제합니다.
    """
    try:
        # 프로젝트 ID로 프로젝트 조회
        project = Project.query.get(project_id)
        
        if not project:
            return jsonify({
                'success': False,
                'message': '존재하지 않는 프로젝트입니다.'
            }), 404
        
        # 프로젝트에 연결된 이메일 히스토리 삭제
        EmailHistory.query.filter_by(project_id=project_id).delete()
        
        # 프로젝트에 연결된 상태 히스토리 삭제
        StatusHistory.query.filter_by(project_id=project_id).delete()
        
        # 프로젝트 삭제
        db.session.delete(project)
        db.session.commit()
        
        # 파일 시스템에서 관련 파일들도 삭제 (보고서, 첨부파일 등)
        project_upload_dir = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), str(project_id))
        if os.path.exists(project_upload_dir):
            import shutil
            shutil.rmtree(project_upload_dir)
        
        return jsonify({
            'success': True,
            'message': '프로젝트가 성공적으로 삭제되었습니다.'
        })
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"프로젝트 삭제 중 오류 발생: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'프로젝트 삭제 중 오류가 발생했습니다: {str(e)}'
        }), 500

@bp.route('/project/<project_id>/extend', methods=['POST'])
async def extend_project(project_id):
    """프로젝트 기간 연장 처리"""
    try:
        project = Project.query.get_or_404(project_id)
        data = request.json
        
        new_date = data.get('new_date')
        reason = data.get('reason')
        date_difference = data.get('date_difference', '계산되지 않음')
        
        if not new_date:
            return jsonify({'success': False, 'message': '새로운 완료 예정일이 필요합니다.'}), 400
            
        if not reason:
            return jsonify({'success': False, 'message': '연장 사유가 필요합니다.'}), 400
        
        # 날짜 유효성 검사
        try:
            new_date_obj = datetime.strptime(new_date, '%Y-%m-%d')
            today = get_korea_time().date()
            
            # 과거 날짜 검사
            if new_date_obj.date() < today:
                return jsonify({'success': False, 'message': '과거 날짜로 연장할 수 없습니다.'}), 400
                
            # 현재 예상 완료일보다 이전 날짜인지 검사
            if project.expected_report_date and new_date_obj.date() <= project.expected_report_date.date():
                return jsonify({'success': False, 'message': '현재 예상 완료일보다 이후 날짜를 선택해주세요.'}), 400
                
        except ValueError:
            return jsonify({'success': False, 'message': '유효하지 않은 날짜 형식입니다.'}), 400
        
        # 프로젝트 상태 기록
        old_status = project.status
        
        # 이메일 데이터 준비
        email_data = {
            'current_date': project.expected_report_date.strftime('%Y-%m-%d') if project.expected_report_date else '미정',
            'new_date': new_date,
            'reason': reason,
            'date_difference': date_difference
        }
        
        # 이메일 발송
        success, error_message = await send_mail(
            project.email,
            f"RTM AI POC 기간 연장 안내 - {project.company}",
            render_template(
                'email/online-poc-email-delay.html',
                프로젝트ID=project.id,
                이름=project.name,
                회사명=project.company,
                유형=project.project_type,
                기존예정일=email_data['current_date'],
                변경예정일=email_data['new_date'],
                지연일수=date_difference.replace('일', '').strip() if date_difference and '일' in date_difference else date_difference,
                변경사유=email_data['reason'],
                프로젝트관리페이지=project.project_url
            )
        )
        
        # 이메일 로그 추가
        email_log = EmailHistory(
            project_id=project.id,
            email_type=EmailType.DELAY,
            subject=f"RTM AI POC 기간 연장 안내 - {project.company}",
            recipient=project.email,
            status='success' if success else 'failed',
            error_message=error_message if not success else None
        )
        db.session.add(email_log)
        
        # 이메일 발송 성공한 경우에만 상태 업데이트
        if success:
            # 프로젝트 상태 및 완료 예정일 업데이트
            project.status = ProjectStatus.DELAYED
            project.expected_report_date = new_date_obj
            
            # 상태 이력 추가
            status_history = StatusHistory(
                project_id=project.id,
                previous_status=old_status,
                new_status=ProjectStatus.DELAYED,
                created_by='System',
                reason=f"기간 연장: {reason} (연장일수: {date_difference})"
            )
            db.session.add(status_history)
            
            # 변경사항 저장
            db.session.commit()
            
            return jsonify({
                'success': True, 
                'message': '이메일이 성공적으로 발송되었으며, 프로젝트 기간이 연장되었습니다.',
                'new_date': new_date
            })
        else:
            # 이메일 발송 실패 시 DB 변경사항 없이 로그만 저장
            db.session.commit()  # 이메일 로그만 저장
            return jsonify({
                'success': False, 
                'message': f'이메일 발송에 실패했습니다: {error_message}. 프로젝트 상태가 변경되지 않았습니다.'
            }), 500
            
    except Exception as e:
        db.session.rollback()
        logging.error(f"기간 연장 중 오류 발생: {str(e)}")
        return jsonify({'success': False, 'message': f'오류가 발생했습니다: {str(e)}'}), 500

@bp.route('/project/<project_id>/report/upload', methods=['POST'])
async def upload_report(project_id):
    """리포트 업로드 및 완료 처리"""
    try:
        project = Project.query.get_or_404(project_id)
        
        # 1. 파일 업로드 처리
        if 'report_file' not in request.files:
            return jsonify({'success': False, 'message': '리포트 파일이 필요합니다.'}), 400
            
        report_file = request.files['report_file']
        comment = request.form.get('comment', '')
        
        if report_file.filename == '':
            return jsonify({'success': False, 'message': '선택된 파일이 없습니다.'}), 400
            
        if not allowed_file(report_file.filename, ['pdf']):
            return jsonify({'success': False, 'message': 'PDF 파일만 업로드 가능합니다.'}), 400
        
        # 파일 저장
        upload_folder = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_folder, exist_ok=True)
        
        # 안전한 파일명으로 변환
        filename = secure_filename(report_file.filename)
        # 고유한 파일명 생성 (UUID + 원래 파일명)
        unique_filename = f"{project_id}_{filename}"
        file_path = os.path.join(upload_folder, unique_filename)
        
        # 파일 저장
        report_file.save(file_path)
        
        # 2. 이메일 발송 데이터 준비
        email_data = {
            'report_name': filename,
            'comment': comment
        }
        
        # 3. 이메일 발송
        success, error_message = await send_poc_complete_mail(project, email_data)
        
        if not success:
            # 이메일 전송 실패 시 파일은 저장되지만 상태 변경은 하지 않음
            return jsonify({
                'success': False, 
                'message': f'리포트가 업로드되었지만 이메일 발송에 실패했습니다: {error_message}. 상태 변경이 취소되었습니다.'
            }), 500
        
        # 4. 이메일 발송 성공 시 프로젝트 상태 업데이트
        old_status = project.status
        project.status = ProjectStatus.COMPLETED
        project.report_file = unique_filename
        project.completed_at = datetime.utcnow()
        
        # 5. 상태 이력 추가
        status_history = StatusHistory(
            project_id=project.id,
            previous_status=old_status,
            new_status=ProjectStatus.COMPLETED,
            created_by='System',
            reason=f"리포트 업로드 및 완료 처리: {comment if comment else '(코멘트 없음)'}"
        )
        
        db.session.add(status_history)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': '리포트가 성공적으로 업로드되었으며, 이메일이 발송되었습니다. 프로젝트가 완료 처리되었습니다.'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"리포트 업로드 중 오류 발생: {str(e)}")
        return jsonify({'success': False, 'message': f"오류가 발생했습니다: {str(e)}"}), 500

async def send_delay_mail(project, email_data):
    """지연 안내 이메일 발송"""
    try:
        # 지연일수 확인
        date_difference = email_data.get('date_difference', '').replace('일', '').strip()
        if not date_difference or not date_difference.isdigit():
            # 날짜 차이가 없거나 숫자가 아닌 경우 계산
            current_date = email_data.get('current_date', '')
            new_date = email_data.get('new_date', '')
            delay_days = calculate_days_difference(current_date, new_date)
        else:
            delay_days = date_difference
        
        # 이메일 데이터 준비 - 기존 템플릿 형식으로 변환
        template_data = {
            '프로젝트ID': project.id,
            '이름': project.name,
            '회사명': project.company,
            '유형': project.project_type,
            '기존예정일': email_data.get('current_date', ''),
            '변경예정일': email_data.get('new_date', ''),
            '지연일수': delay_days,
            '변경사유': email_data.get('reason', ''),
            '프로젝트관리페이지': project.project_url,
        }
        
        # 이메일 내용 준비
        html = render_template(
            'email/online-poc-email-delay.html',
            **template_data
        )
        
        # 이메일 발송
        subject = f"RTM AI POC 기간 연장 안내 - {project.company}"
        success, error_message = await send_mail(project.email, subject, html)
        
        # 이메일 로그 추가
        email_log = EmailHistory(
            project_id=project.id,
            email_type=EmailType.DELAY,
            subject=subject,
            recipient=project.email,
            status='success' if success else 'failed',
            error_message=error_message if not success else None
        )
        
        db.session.add(email_log)
        db.session.commit()
        
        logging.info(f"지연 안내 이메일 발송 {'성공' if success else '실패'}: {project.id}")
        return success
        
    except Exception as e:
        logging.error(f"지연 안내 이메일 발송 중 오류: {str(e)}")
        return False

async def send_poc_complete_mail(project, email_data):
    """POC 완료 이메일 발송"""
    try:
        # 이메일 데이터 준비 - 기존 템플릿 형식으로 변환
        template_data = {
            '프로젝트ID': project.id,
            '이름': project.name,
            '회사명': project.company,
            '유형': project.project_type,
            '보고서명': email_data.get('report_name', ''),
            '코멘트': email_data.get('comment', ''),
            '프로젝트관리페이지': project.project_url,
        }
        
        # 이메일 내용 준비
        html = render_template(
            'email/online-poc-email-report.html',
            **template_data
        )
        
        # 이메일 발송
        subject = f"RTM AI POC 완료 보고서 - {project.company}"
        success, error_message = await send_mail(project.email, subject, html)
        
        # 이메일 로그 추가
        email_log = EmailHistory(
            project_id=project.id,
            email_type=EmailType.POC_COMPLETE,
            subject=subject,
            recipient=project.email,
            status='success' if success else 'failed',
            error_message=error_message if not success else None
        )
        
        db.session.add(email_log)
        db.session.commit()
        
        logging.info(f"POC 완료 이메일 발송 {'성공' if success else '실패'}: {project.id}")
        return success, error_message
        
    except Exception as e:
        logging.error(f"POC 완료 이메일 발송 중 오류: {str(e)}")
        return False, str(e)

def calculate_days_difference(date_str1, date_str2):
    """두 날짜 문자열 사이의 일수 차이 계산"""
    try:
        if not date_str1 or not date_str2 or date_str1 == '미정':
            return '미정'
        
        date1 = datetime.strptime(date_str1, '%Y-%m-%d')
        date2 = datetime.strptime(date_str2, '%Y-%m-%d')
        
        delta = date2 - date1
        return str(delta.days)
    except Exception as e:
        logging.error(f"날짜 차이 계산 중 오류: {str(e)}")
        return '계산 불가'
