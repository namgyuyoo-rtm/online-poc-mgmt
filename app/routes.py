from datetime import datetime, timedelta
from app.models import db, Project, ProjectStatus, StatusHistory, ProjectDiscussion, EmailHistory, EmailType, ProjectAction
from flask import Blueprint, render_template, jsonify, request, redirect, url_for, send_file, abort
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

LOGO_BASE64 = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAG0AAAAmCAYAAADOZxX5AAAACXBIWXMAABCcAAAQnAEmzTo0AAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAgPSURBVHgB7VvdTtxGFD5nvLQlihpHCpCoKnGSVupdyBPEeYLAEwAXzd8N5AmAJ2C5qUhu2D4B5AnYPAHJXaWW4KRqy5/EVkrDhqzn9JzZXa9t7MWQ9bKR9pOI1+Oxx55v5pzvnJkA9PHFAbNWPJh1bP/jB5d8dFBh5RNA+drytgd9dB0nkrb76OoUEk0CwRgoXCJlrQ3/8tcr6OPcUEi7sPfoqstkrRCRA4jlGsKd/szqDSTOtL2HI4t8mJXfmnBh5Pn2PPTRMzhG2v7D4RUCnJLfBLA0/GxnFvroKURIC88wJsxjwm5AHz2HwKeJ4ACiYFYh4jT0CG5970ydVAct8HgEVn73vFOJJIdh+eDCGeFbsOZ5XiVefstxxsEHu/luf3heGc6A8LcPWFD+jRszpB08uur4RHMUVMXy0PJ2GXoEhLRyYh1dP94cvV5BoLUBpRbkA0+6T2laJwQHzogCoMeHcrycBdwK2zG78W5C6mU4JYSw8LcfaVzgw7ySEw16kglzggYRfoUvF7b45CNNWzdHRxfbVWyMYgfyANUJa74TtzUOp4WCyaRiM9OI6sKjVdnq2TgMEdb4fV8nlN8moDHuLCdUOntrdNTefPeujak3ozcO7nCaOalNAXegFy9ji2uz7I4WKvO8NciIHx1nzNfkhsvY/F83be4/GB6n2Gjr6eBZ44s3f3qltMs/OI6rxTQ1yJNZx6P85WbCPZspzxE/pzTMZG0zAXa8gAhcebesvs3XeiYt96F4GLnhAkwYOZ3E7pOhMcgR0ika8R5/SEscKJqELmIggTSB1jqTiZRBAxCzfnJ/wy8q9l+3oYtQ2sqVNIEnAoRwqXkuo/wn0xHdAaWQxkRMGtN5AtLUrEK6ZI5M31i2BjsDFj13oQtAgoiJr+UlOE4Hm83u1EmVWDHOJZY3uFFNWRp+8D8cAkBO4KntQhfAsVEFzgnkR/uUY95y6zfdb3ev+D0IDzAMuStqkpYAtsku5ACJB6k3RnzeiJDGLuhF8LshSNJuZL/X8r9CGLbMfBOK2Ts2IonycdxsoqbyFjpNRD6+3nbXFDFZEdI8FhClsDDi/k00f8cECBOGfoQfR/5RkenXgnvQYRMpi6iyLkf1DEKuqI/k1scjYCkp1ZQbdHSmmbZjwihJkBSMzG/hq5S4TvHIf5l0oUbUNptwWujqhxkxjRwAv4acIGRJFkRzaipcPqBgAc4J2JgUWkExXK60PrZ6ogGDkEAGmqThJG8ZriMqmHUBpkXp4/uPr3bETMqCKq/LzZuXSW/vVLg56sxynnEr9Ed1sjDSGahwOksOspNI8tsy28KChN8sMqviKTVU6alEVahWXyX5NdO4puLuk+8+K646+HloDDWtmufxu3cqEc0jt9RIGDiQ0EnSQUrhvU3vVJmMXMGzLjzj7YggCecZsbUqUItpgKqEDZdLlYrs/YBk2OjXNrYfjJxpIXT/8dCkj0qy6HbjrTtmpmTkWogTkcwH1M2KIeutd++syyGfC/Y514MTavlw8z4hDdEUJCJA+LfbLMc2/VQQ0syParWYNtsEFsIiL5Cui5mDDNjl2SX1SatSkzCzqLq8XYIOwqydxT8QyT4vsjKBMDB7IkgkMcz+raUmmdSYdYjwIgG2yfLLbGNCJvgp622ac/m6u/9wxOMb11DRS40Dnq9981BLWTbWai43eh8S4jxf8oE54I3nFW9dd+7ySDVOnDtiXPzdm3deEc4J/C6BMuS+ehu+JoJEESejG4FyjQUJz6z70FgUQAr7vbpFYX/dKvAbM01gfE0G89VwsrOkcVVMZ4FoS/7kNxMmitM9dg+vgue5k8tHmI6GLjQnIxjOD6mpwIb8D2Ybm/PJ8NpbFqVrSJOYbO/B8BwTN9+WODGhfP394ODloWc7WEO8Yeq3Ma187amYRdl/IrEa5IDAv7Vg81rUapbkbC6IpgaP9Y1SyfEXC5VyitINymSV3ZBmYjLE+SZxMjMoplrkvKbwDtvT0sXDwznxWTzDZuRcyuPEmfvZJA493ynKDi8umq19OJyCnGD8m8KnoSLH0rqjsWZmhGYOJgxo8blR+d+snCoII6ibx5a6m2cyVjn3WBYfxOQF01gpeqpQy2rqBtR3bLlyZMI3jD8Dmm69Myz9NzgoBHv8vI3mljzu1FxHvvi3cGdIu+Lf4DyRlrhGWIqdiwBJi2FDz9B1n8ajIZylGPdZkFhMCpu1KWMC2cRZpF5ZGhcpYVVA+bVV68KFstQT0yl7Jb89PJxsEBz4FupC3pH920Tcv3VzLc2JtYWQTJohKBSutJP5fK1VD9QlQ1o8KyJiQ7aEs1LcknMxcZ+YxLQMvZT71eq41LtYrY7JfZwkLYYJFsL8hF1LnYb4NxXd/mcfcabk3PxbO4TykQNt+4YixBvJL8qRzZgQNx6pymQU6kR5TGLbdSCGLG6WIIVcns1L156dTUGyDA5IkL1/J9UXn8HZhnu8ruU0y76pK7qsSePKadtMu7fQxrqI/Ld8E3xX2qXaUHydDpZ3KsHOkYMp26598/UqM+U2y2R2DLBvulz0OI4bWQ9fS3hw6cry9rQJwGPxXv//A3QWQZwmAfbQ8o6IDxkla+ZP6wkhTK6zU3/b7kGa6F85yqw1z2BBwMeSKMg+YZ0FZq24J/nHevCc/CCyJq48/7sjGfw+2kNlrVg4+lhKU39S3iese8hMmlkNYHOZFHTnlVfsIxmZzWMTslPLMoE18ToZeO8vDJZuFLu4lN8H/A88yJ7V1te3qQAAAABJRU5ErkJggg=='

# 중앙화된 이메일 설정
EMAIL_CONFIG = {
    # 각 이메일 타입별 설정
    EmailType.APPLICATION_COMPLETE: {
        'template': 'email/online-poc-email-welcome.html',
        'subject': 'RTM AI POC 신청 완료 안내',
        'page_template': 'mail/application-complete.html',
        'status': ProjectStatus.APPLICATION_COMPLETE
    },
    EmailType.SUBMISSION_COMPLETE: {
        'template': 'email/online-poc-email-complete.html',
        'subject': 'RTM AI POC 제출 완료 안내',
        'page_template': 'mail/submission-complete.html',
        'status': ProjectStatus.RECEPTION_COMPLETE
    },
    EmailType.CANCELLATION: {
        'template': 'email/online-poc-email-cancel.html',
        'subject': 'RTM AI POC 취소 안내',
        'page_template': 'mail/cancel_mail.html',
        'status': ProjectStatus.CANCELLED
    },
    EmailType.DELAY: {
        'template': 'email/online-poc-email-delay.html',
        'subject': 'RTM AI POC 기간 연장 안내',
        'page_template': 'mail/extend_mail.html',
        'status': ProjectStatus.POC_IN_PROGRESS
    },
    EmailType.REPORT: {
        'template': 'email/online-poc-email-complete.html',
        'subject': 'RTM AI POC 완료 안내',
        'page_template': 'mail/complete_mail.html',
        'status': ProjectStatus.POC_COMPLETE
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
        if config.get('status') and project.status != config['status']:
            logger.error(f"현재 상태({project.status.value})에서는 이메일을 발송할 수 없습니다. {config['status'].value} 상태여야 합니다.")
            return False, f"현재 상태({project.status.value})에서는 이메일을 발송할 수 없습니다"
        
        # 이메일 생성
        msg = MIMEMultipart('alternative')
        msg['Subject'] = config['subject']
        msg['From'] = os.getenv('SMTP_FROM')
        msg['To'] = project.email
        
        # 템플릿 데이터 준비
        data = {
            '접수시각': project.created_at.strftime('%Y-%m-%d %H:%M'),
            '이름': project.name,
            '회사명': project.company,
            '이메일': project.email,
            '연락처': project.phone,
            '유형': project.project_type,
            '프로젝트ID': project.id,
            '프로젝트관리페이지': os.getenv('APP_URL', 'http://localhost:5000') + f'/project/{project.id}',
            '과제목적': project.purpose
        }
        
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
            project_id=project.id,
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
                project_id=project.id,
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
    return render_template('main.html')

@bp.route('/submission-complete', methods=['GET', 'POST'])
async def submission_complete():
    form = POCRequestForm()
    preview_url = 'email/online-poc-email-complete.html'
    if form.validate_on_submit():
        project = Project(
            id=form.project_id.data,
            name=form.name.data,
            company=form.company.data,
            email=form.email.data,
            phone=form.phone.data,
            project_type=form.project_type.data,
            purpose=form.purpose.data,
            project_url=form.project_url.data,
            status=ProjectStatus.RECEPTION_COMPLETE
        )
        db.session.add(project)
        db.session.commit()
        
        success, error = await send_email(
            project=project,
            email_type=EmailType.SUBMISSION_COMPLETE
        )
        
        if not success:
            # 이메일 발송 실패 시 이미 send_email 함수에서 이력을 기록하므로 여기서는 불필요
            return render_template('submission_complete.html', form=form, preview_url=preview_url, error=error)

            return redirect(url_for('main.projects'))

    return render_template('submission_complete.html', form=form, preview_url=preview_url)

@bp.route('/application-complete', methods=['GET', 'POST'])
async def application_complete():
    form = POCRequestForm()
    preview_url = 'email/online-poc-email-welcome.html'
    if form.validate_on_submit():
        project = Project.query.get(form.project_id.data)
        if project:
            # 상태를 APPLICATION_COMPLETE로 변경
            old_status = project.status
            project.status = ProjectStatus.APPLICATION_COMPLETE
            
            # 상태 변경 이력 저장
            status_history = StatusHistory(
                project_id=project.id,
                previous_status=old_status,
                new_status=ProjectStatus.APPLICATION_COMPLETE,
                created_by='System',
                reason='신청 완료 처리'
            )
            db.session.add(status_history)
            
            success, error = await send_email(
                project=project,
                email_type=EmailType.APPLICATION_COMPLETE
            )
            
            if not success:
                return render_template('application_complete.html', form=form, preview_url=preview_url, error=error)

                return redirect(url_for('main.projects'))

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
        
        return render_template('projects.html', projects=projects)
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
    form_data['접수시각'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 이메일 템플릿 렌더링
    template_loader = jinja2.FileSystemLoader(searchpath='app/templates')
    template_env = jinja2.Environment(loader=template_loader)
    
    # 이메일 타입에 따른 템플릿 선택
    template_paths = {
        'submission-complete': 'email/online-poc-email-complete.html',
        'application-complete': 'email/online-poc-email-welcome.html',
        'cancellation': 'email/online-poc-email-cancel.html',
        'delay': 'email/online-poc-email-delay.html',
        'report': 'email/online-poc-email-report.html'
    }
    
    # If no email_type provided, default to application-complete
    template_path = template_paths.get(email_type or 'application-complete')
    if not template_path:
        return jsonify({'error': 'Invalid email type'}), 400
        
    template = template_env.get_template(template_path)
    html_content = template.render(**form_data)
    
    return html_content

@bp.route('/send', methods=['POST'])
async def send():
    try:
        data = request.get_json()
        
        # 데이터 로깅 추가
        logging.info(f"Received data: {data}")
        
        # 필수 필드 검사 (project_id 추가)
        required_fields = ['name', 'company', 'email', 'phone', 'project_type', 'project_id']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False, 
                    'message': f'필수 필드가 누락되었습니다: {field}'
                }), 400

        # 새 프로젝트 생성 (project_id를 입력값으로 사용)
        new_project = Project(
            id=data['project_id'],  # 자동 생성 대신 입력값 사용
            name=data['name'],
            company=data['company'],
            email=data['email'],
            phone=data['phone'],
            project_type=data['project_type'],
            purpose=data.get('purpose', ''),
            project_url=data.get('project_url', ''),
            status=ProjectStatus.APPLICATION_COMPLETE
        )
        
        # 데이터베이스에 저장
        db.session.add(new_project)
        db.session.commit()
        
        # 이메일 전송
        success, error_msg = await send_email(
            project=new_project,
            email_type=EmailType.APPLICATION_COMPLETE
        )
        
        if success:
            return jsonify({
                'success': True, 
                'message': '이메일이 성공적으로 전송되었습니다.',
                'project_id': data['project_id']
            })
        else:
            return jsonify({
                'success': False, 
                'message': error_msg or '이메일 전송에 실패했습니다.'
            }), 500
            
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error in send route: {str(e)}")
        return jsonify({
            'success': False, 
            'message': f'서버 오류가 발생했습니다: {str(e)}'
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
        
        return render_template('project_detail.html', project=project)
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
    """이메일 발송 API 엔드포인트"""
    try:
        project = Project.query.get_or_404(project_id)
        
        # Convert hyphenated URL format to enum format
        email_type_enum = email_type.upper().replace('-', '_')
        
        try:
            # Get the correct email type from the enum
            email_type_obj = EmailType[email_type_enum]
            
            # 이메일 발송
            success, error_msg = await send_email(project, email_type_obj)
            
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
        except KeyError:
            return jsonify({
                'success': False,
                'message': '잘못된 이메일 타입입니다.',
                'type': 'invalid_email_type'
            }), 400

    except Exception as e:
        logger.error(f"이메일 발송 중 오류: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'이메일 발송 중 오류가 발생했습니다: {str(e)}',
            'type': 'server_error'
        }), 500

@bp.route('/project/<project_id>/mail/<email_type>')
def send_email_page(project_id, email_type):
    """이메일 발송 페이지 라우트"""
    try:
        project = Project.query.get_or_404(project_id)
        form = EmailForm(obj=project)
        
        # Convert hyphenated URL format to enum format
        email_type_enum = email_type.upper().replace('-', '_')
        
        try:
            # Get the correct email type from the enum
            email_type_obj = EmailType[email_type_enum]
            # Get the email configuration from the centralized config
            if email_type_obj not in EMAIL_CONFIG:
                logger.error(f"지원되지 않는 이메일 타입: {email_type}")
                abort(400, f"지원되지 않는 이메일 타입: {email_type}")
            
            config = EMAIL_CONFIG[email_type_obj]
            
            return render_template(
                config['page_template'],
                form=form,
                project=project,
                email_type=email_type_obj
            )
        except KeyError:
            logger.error(f"Invalid email type: {email_type}")
            abort(400, f"Invalid email type: {email_type}")
        
    except Exception as e:
        logger.error(f"이메일 발송 페이지 로드 중 오류: {str(e)}")
        abort(500, str(e))

@bp.route('/project/<project_id>/mail/submission-complete')
def send_submission_complete_mail_page(project_id):
    """접수 완료 이메일 발송 페이지"""
    project = Project.query.get_or_404(project_id)
    form = EmailForm(obj=project)
    return render_template(
        EMAIL_CONFIG[EmailType.SUBMISSION_COMPLETE]['page_template'],
        form=form, 
        project=project,
        email_type=EmailType.SUBMISSION_COMPLETE
    )

@bp.route('/project/<project_id>/mail/application-complete')
def send_application_complete_mail_page(project_id):
    """신청 완료 이메일 발송 페이지"""
    project = Project.query.get_or_404(project_id)
    form = EmailForm(obj=project)
    return render_template(
        EMAIL_CONFIG[EmailType.APPLICATION_COMPLETE]['page_template'],
                         form=form, 
                         project=project,
        email_type=EmailType.APPLICATION_COMPLETE
    )

@bp.route('/project/<project_id>/mail/delay')
def send_delay_mail_page(project_id):
    """기간 연장 이메일 발송 페이지"""
    project = Project.query.get_or_404(project_id)
    form = EmailForm(obj=project)
    return render_template(
        EMAIL_CONFIG[EmailType.DELAY]['page_template'],
                         form=form, 
                         project=project,
        email_type=EmailType.DELAY
    )

@bp.route('/project/<project_id>/mail/report')
def send_report_mail_page(project_id):
    """리포트 이메일 발송 페이지"""
    project = Project.query.get_or_404(project_id)
    form = EmailForm(obj=project)
    return render_template(
        EMAIL_CONFIG[EmailType.REPORT]['page_template'],
                         form=form, 
                         project=project,
        email_type=EmailType.REPORT
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
    return render_template(EMAIL_CONFIG[EmailType.REPORT]['page_template'],
                         form=form, 
                         project=project,
                         email_type=EmailType.REPORT)

@bp.route('/project/<project_id>/status', methods=['POST'])
def update_project_status(project_id):
    try:
        data = request.get_json()
        project = Project.query.get_or_404(project_id)
        
        new_status = ProjectStatus[data['status']]
        old_status = project.status
        
        # 상태 업데이트
        project.status = new_status
        
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
        
        return jsonify({'success': True, 'message': '상태가 성공적으로 변경되었습니다.'})
        
    except KeyError:
        return jsonify({'success': False, 'message': '잘못된 상태값입니다.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

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
            download_name=f'POC_Report_{project.company}_{datetime.now().strftime("%Y%m%d")}.pdf'
        )
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
