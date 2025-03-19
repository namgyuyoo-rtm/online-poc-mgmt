from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, URL
import os
import tempfile
from datetime import datetime
from jinja2 import Template
from dotenv import load_dotenv
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import asyncio
from flask_sqlalchemy import SQLAlchemy
from enum import Enum
import json
import jinja2
import uuid
import logging

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('email_logs.txt', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ProjectStatus(Enum):
    INITIAL_REQUEST = "initial_request"
    APPLICATION_COMPLETE = "application_complete"
    RECEPTION_COMPLETE = "reception_complete"
    CANCELLED = "cancelled"
    COMPLETED = "completed"

class EmailType(Enum):
    WELCOME = "welcome"
    APPLICATION_COMPLETE = "application_complete"
    RECEPTION_COMPLETE = "reception_complete"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    ADDITIONAL = "additional"
    REPORT = "report"

class Project(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    company = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    project_type = db.Column(db.String(50), nullable=False)
    purpose = db.Column(db.Text)
    project_url = db.Column(db.String(200), nullable=False)
    status = db.Column(db.Enum(ProjectStatus), default=ProjectStatus.INITIAL_REQUEST)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class EmailHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.String(36), db.ForeignKey('project.id'), nullable=False)
    email_type = db.Column(db.Enum(EmailType), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), nullable=False)  # success, failed
    error_message = db.Column(db.Text)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    project = db.relationship('Project', backref=db.backref('email_history', lazy=True))

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

def generate_html_preview(data):
    """Generate HTML preview and save to temporary file"""
    # Read template
    with open('templates/online-poc-email-welcome.html', 'r', encoding='utf-8') as f:
        template = Template(f.read())

    # Add timestamp
    data['접수시각'] = datetime.now().strftime('%Y-%m-%d %H:%M')

    # Render template with data
    html_content = template.render(**data)
    
    # Create temporary file
    temp_dir = tempfile.gettempdir()
    preview_file = os.path.join(temp_dir, 'poc_welcome_preview.html')
    
    # Save HTML content
    with open(preview_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return preview_file

async def send_email(to_email, data):
    """Send email using SMTP"""
    try:
        logger.info(f"Attempting to send email to {to_email}")
        logger.info(f"SMTP settings - Host: {os.getenv('SMTP_HOST')}, Port: {os.getenv('SMTP_PORT')}, From: {os.getenv('SMTP_FROM')}")
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'RTM AI POC 신청 완료 안내'
        msg['From'] = os.getenv('SMTP_FROM')
        msg['To'] = to_email

        # Read template
        logger.info("Reading email template")
        with open('templates/online-poc-email-welcome.html', 'r', encoding='utf-8') as f:
            template = Template(f.read())

        # Add timestamp
        data['접수시각'] = datetime.now().strftime('%Y-%m-%d %H:%M')

        # Render template with data
        logger.info("Rendering email template")
        html_content = template.render(**data)

        # Attach HTML content
        msg.attach(MIMEText(html_content, 'html'))

        # Send email
        logger.info("Connecting to SMTP server")
        smtp = aiosmtplib.SMTP(
            hostname=os.getenv('SMTP_HOST'),
            port=int(os.getenv('SMTP_PORT')),
            use_tls=os.getenv('SMTP_SECURE', 'true').lower() == 'true'
        )

        logger.info("Establishing SMTP connection")
        await smtp.connect()
        logger.info("Logging in to SMTP server")
        await smtp.login(os.getenv('SMTP_USER'), os.getenv('SMTP_PASSWORD'))
        logger.info("Sending email")
        await smtp.send_message(msg)
        logger.info("Closing SMTP connection")
        await smtp.quit()

        logger.info("Email sent successfully")
        return True, None
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False, str(e)

async def send_status_email(project, template_name, subject):
    """Send status update email using specified template"""
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = os.getenv('SMTP_FROM')
        msg['To'] = project.email

        # Read template
        with open(f'templates/{template_name}.html', 'r', encoding='utf-8') as f:
            template = Template(f.read())

        # Prepare data for template
        data = {
            '접수시각': project.created_at.strftime('%Y-%m-%d %H:%M'),
            '이름': project.name,
            '회사명': project.company,
            '이메일': project.email,
            '연락처': project.phone,
            '유형': project.project_type,
            '프로젝트ID': project.id,
            '프로젝트관리페이지': project.project_url,
            '과제목적': project.purpose
        }

        # Render template with data
        html_content = template.render(**data)
        msg.attach(MIMEText(html_content, 'html'))

        # Send email
        smtp = aiosmtplib.SMTP(
            hostname=os.getenv('SMTP_HOST'),
            port=int(os.getenv('SMTP_PORT')),
            use_tls=os.getenv('SMTP_SECURE', 'true').lower() == 'true'
        )

        await smtp.connect()
        await smtp.login(os.getenv('SMTP_USER'), os.getenv('SMTP_PASSWORD'))
        await smtp.send_message(msg)
        await smtp.quit()

        # Record successful email
        email_type = EmailType(template_name.split('-')[-1])
        history = EmailHistory(
            project_id=project.id,
            email_type=email_type,
            subject=subject,
            status='success'
        )
        db.session.add(history)
        db.session.commit()

        return True, None
    except Exception as e:
        # Record failed email
        email_type = EmailType(template_name.split('-')[-1])
        history = EmailHistory(
            project_id=project.id,
            email_type=email_type,
            subject=subject,
            status='failed',
            error_message=str(e)
        )
        db.session.add(history)
        db.session.commit()
        return False, str(e)

@app.route('/', methods=['GET', 'POST'])
def index():
    form = POCRequestForm()
    preview_url = None
    
    if form.validate_on_submit():
        # Convert form data to dictionary
        data = {
            '이름': form.name.data,
            '회사명': form.company.data,
            '이메일': form.email.data,
            '연락처': form.phone.data,
            '유형': form.project_type.data,
            '프로젝트ID': form.project_id.data,
            '프로젝트관리페이지': form.project_url.data,
            '과제목적': form.purpose.data,
            '접수시각': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Generate preview
        preview_file = generate_html_preview(data)
        preview_url = f'/preview/{os.path.basename(preview_file)}'
    
    return render_template('index.html', form=form, preview_url=preview_url)

@app.route('/preview/<filename>')
def preview(filename):
    temp_dir = tempfile.gettempdir()
    return send_file(os.path.join(temp_dir, filename))

@app.route('/send', methods=['POST'])
async def send():
    try:
        logger.info("Received email send request")
        data = request.json
        if not data or '이메일' not in data:
            logger.error("Missing email address in request")
            return jsonify({'status': 'error', 'message': '이메일 주소가 필요합니다.'}), 400

        logger.info(f"Sending email to {data['이메일']}")
        success, error = await send_email(data['이메일'], data)
        if success:
            logger.info("Email sent successfully")
            return jsonify({'status': 'success', 'message': '이메일이 성공적으로 발송되었습니다.'})
        else:
            logger.error(f"Failed to send email: {error}")
            return jsonify({'status': 'error', 'message': f'이메일 발송 중 오류가 발생했습니다: {error}'}), 500
    except Exception as e:
        logger.error(f"Error in send route: {str(e)}")
        return jsonify({'status': 'error', 'message': f'처리 중 오류가 발생했습니다: {str(e)}'}), 500

@app.route('/api/project/initial-request', methods=['POST'])
async def initial_request():
    """Handle initial POC request"""
    try:
        data = request.json
        project = Project(
            id=data['프로젝트ID'],
            name=data['이름'],
            company=data['회사명'],
            email=data['이메일'],
            phone=data['연락처'],
            project_type=data['유형'],
            purpose=data['과제목적'],
            project_url=data['프로젝트관리페이지']
        )
        
        db.session.add(project)
        db.session.commit()
        
        success, error = await send_status_email(
            project,
            'online-poc-email-welcome',
            'RTM AI POC 신청 완료 안내'
        )
        
        if success:
            return jsonify({'status': 'success', 'message': '초기 신청이 완료되었습니다.'})
        else:
            return jsonify({'status': 'error', 'message': f'이메일 발송 중 오류가 발생했습니다: {error}'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'처리 중 오류가 발생했습니다: {str(e)}'}), 500

@app.route('/api/project/complete', methods=['POST'])
async def complete_application():
    """Handle POC application completion"""
    try:
        data = request.json
        project = Project.query.get(data['프로젝트ID'])
        
        if not project:
            return jsonify({'status': 'error', 'message': '프로젝트를 찾을 수 없습니다.'}), 404
        
        project.status = ProjectStatus.APPLICATION_COMPLETE
        db.session.commit()
        
        success, error = await send_status_email(
            project,
            'online-poc-email-complete',
            'RTM AI POC 접수 완료 안내'
        )
        
        if success:
            return jsonify({'status': 'success', 'message': '신청이 완료되었습니다.'})
        else:
            return jsonify({'status': 'error', 'message': f'이메일 발송 중 오류가 발생했습니다: {error}'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'처리 중 오류가 발생했습니다: {str(e)}'}), 500

@app.route('/api/project/cancel', methods=['POST'])
async def cancel_project():
    """Handle project cancellation"""
    try:
        data = request.json
        project = Project.query.get(data['프로젝트ID'])
        
        if not project:
            return jsonify({'status': 'error', 'message': '프로젝트를 찾을 수 없습니다.'}), 404
        
        project.status = ProjectStatus.CANCELLED
        db.session.commit()
        
        success, error = await send_status_email(
            project,
            'online-poc-email-cancel',
            'RTM AI POC 신청 취소 안내'
        )
        
        if success:
            return jsonify({'status': 'success', 'message': '프로젝트가 취소되었습니다.'})
        else:
            return jsonify({'status': 'error', 'message': f'이메일 발송 중 오류가 발생했습니다: {error}'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'처리 중 오류가 발생했습니다: {str(e)}'}), 500

@app.route('/api/project/complete-report', methods=['POST'])
async def send_completion_report_email():
    """Send completion report"""
    try:
        data = request.json
        project = Project.query.get(data['프로젝트ID'])
        
        if not project:
            return jsonify({'status': 'error', 'message': '프로젝트를 찾을 수 없습니다.'}), 404
        
        project.status = ProjectStatus.COMPLETED
        db.session.commit()
        
        success, error = await send_status_email(
            project,
            'online-poc-email-report',
            'RTM AI POC 완료 보고서'
        )
        
        if success:
            return jsonify({'status': 'success', 'message': '완료 보고서가 발송되었습니다.'})
        else:
            return jsonify({'status': 'error', 'message': f'이메일 발송 중 오류가 발생했습니다: {error}'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'처리 중 오류가 발생했습니다: {str(e)}'}), 500

@app.route('/preview', methods=['POST'])
def preview_real_time():
    form_data = request.get_json()
    form_data['접수시각'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 이메일 템플릿 렌더링
    template_loader = jinja2.FileSystemLoader('templates')
    template_env = jinja2.Environment(loader=template_loader)
    template = template_env.get_template('online-poc-email-welcome.html')
    html_content = template.render(**form_data)
    
    return html_content

@app.route('/main')
def main():
    return render_template('main.html')

@app.route('/api/project/<project_id>')
def get_project(project_id):
    project = Project.query.get(project_id)
    if project:
        return jsonify({
            'status': 'success',
            'project': {
                'id': project.id,
                'name': project.name,
                'company': project.company,
                'email': project.email,
                'phone': project.phone,
                'project_type': project.project_type,
                'purpose': project.purpose,
                'project_url': project.project_url,
                'status': project.status.value,
                'created_at': project.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        })
    return jsonify({'status': 'error', 'message': '프로젝트를 찾을 수 없습니다.'})

@app.route('/api/project/<project_id>/status', methods=['POST'])
async def update_project_status(project_id):
    project = Project.query.get(project_id)
    if not project:
        return jsonify({'status': 'error', 'message': '프로젝트를 찾을 수 없습니다.'})
    
    data = request.get_json()
    new_status = data.get('status')
    
    if new_status not in [status.value for status in ProjectStatus]:
        return jsonify({'status': 'error', 'message': '잘못된 상태값입니다.'})
    
    project.status = ProjectStatus(new_status)
    db.session.commit()
    
    # 상태 변경에 따른 이메일 발송
    email_subjects = {
        'application_complete': 'RTM AI POC 신청 완료 안내',
        'reception_complete': 'RTM AI POC 접수 완료 안내',
        'cancelled': 'RTM AI POC 신청 취소 안내',
        'completed': 'RTM AI POC 완료 안내'
    }
    
    if new_status in email_subjects:
        await send_status_email(project, f'online-poc-email-{new_status}', email_subjects[new_status])
    
    return jsonify({'status': 'success', 'message': '상태가 업데이트되었습니다.'})

@app.route('/api/project/<project_id>/additional-email', methods=['POST'])
async def send_additional_email(project_id):
    project = Project.query.get(project_id)
    if not project:
        return jsonify({'status': 'error', 'message': '프로젝트를 찾을 수 없습니다.'})
    
    data = request.get_json()
    message = data.get('message')
    
    if not message:
        return jsonify({'status': 'error', 'message': '메시지를 입력해주세요.'})
    
    # 추가 안내 메일 템플릿 렌더링
    template_loader = jinja2.FileSystemLoader('templates')
    template_env = jinja2.Environment(loader=template_loader)
    template = template_env.get_template('online-poc-email-additional.html')
    html_content = template.render(
        project=project,
        message=message
    )
    
    # 이메일 발송
    msg = MIMEMultipart('alternative')
    msg['Subject'] = 'RTM AI POC 추가 안내'
    msg['From'] = os.getenv('SMTP_FROM')
    msg['To'] = project.email
    
    msg.attach(MIMEText(html_content, 'html'))
    
    smtp = aiosmtplib.SMTP(
        hostname=os.getenv('SMTP_HOST'),
        port=int(os.getenv('SMTP_PORT')),
        use_tls=os.getenv('SMTP_SECURE', 'true').lower() == 'true'
    )
    
    await smtp.connect()
    await smtp.login(os.getenv('SMTP_USER'), os.getenv('SMTP_PASSWORD'))
    await smtp.send_message(msg)
    await smtp.quit()
    
    return jsonify({'status': 'success', 'message': '추가 안내 메일이 발송되었습니다.'})

@app.route('/api/project/<project_id>/completion-report', methods=['POST'])
async def send_completion_report(project_id):
    project = Project.query.get(project_id)
    if not project:
        return jsonify({'status': 'error', 'message': '프로젝트를 찾을 수 없습니다.'})
    
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': '파일이 없습니다.'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': '파일이 선택되지 않았습니다.'})
    
    if not file.filename.endswith('.pdf'):
        return jsonify({'status': 'error', 'message': 'PDF 파일만 업로드 가능합니다.'})
    
    # 파일 저장
    filename = f"{uuid.uuid4()}.pdf"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    
    # 완료 보고서 이메일 템플릿 렌더링
    template_loader = jinja2.FileSystemLoader('templates')
    template_env = jinja2.Environment(loader=template_loader)
    template = template_env.get_template('online-poc-email-report.html')
    html_content = template.render(project=project)
    
    # 이메일 발송
    msg = MIMEMultipart('alternative')
    msg['Subject'] = 'RTM AI POC 완료 보고서'
    msg['From'] = os.getenv('SMTP_FROM')
    msg['To'] = project.email
    
    msg.attach(MIMEText(html_content, 'html'))
    
    # PDF 파일 첨부
    with open(file_path, 'rb') as f:
        pdf = MIMEApplication(f.read(), _subtype='pdf')
        pdf.add_header('Content-Disposition', 'attachment', filename='completion_report.pdf')
        msg.attach(pdf)
    
    smtp = aiosmtplib.SMTP(
        hostname=os.getenv('SMTP_HOST'),
        port=int(os.getenv('SMTP_PORT')),
        use_tls=os.getenv('SMTP_SECURE', 'true').lower() == 'true'
    )
    
    await smtp.connect()
    await smtp.login(os.getenv('SMTP_USER'), os.getenv('SMTP_PASSWORD'))
    await smtp.send_message(msg)
    await smtp.quit()
    
    # 임시 파일 삭제
    os.remove(file_path)
    
    return jsonify({'status': 'success', 'message': '완료 보고서가 발송되었습니다.'})

@app.route('/projects')
def project_list():
    projects = Project.query.order_by(Project.created_at.desc()).all()
    return render_template('project_list.html', projects=projects)

@app.route('/api/projects')
def get_projects():
    projects = Project.query.order_by(Project.created_at.desc()).all()
    return jsonify({
        'status': 'success',
        'projects': [{
            'id': project.id,
            'name': project.name,
            'company': project.company,
            'email': project.email,
            'phone': project.phone,
            'project_type': project.project_type,
            'status': project.status.value,
            'created_at': project.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'email_history': [{
                'type': history.email_type.value,
                'subject': history.subject,
                'status': history.status,
                'sent_at': history.sent_at.strftime('%Y-%m-%d %H:%M:%S')
            } for history in project.email_history]
        } for project in projects]
    })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 