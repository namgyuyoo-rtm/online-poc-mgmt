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
import asyncio
from flask_sqlalchemy import SQLAlchemy
from enum import Enum
import json
import jinja2

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-please-change')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///poc.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class ProjectStatus(Enum):
    INITIAL_REQUEST = "initial_request"
    APPLICATION_COMPLETE = "application_complete"
    CANCELLED = "cancelled"
    COMPLETED = "completed"

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

class POCRequestForm(FlaskForm):
    name = StringField('이름', validators=[DataRequired()])
    company = StringField('회사명', validators=[DataRequired()])
    email = StringField('이메일', validators=[DataRequired(), Email()])
    phone = StringField('연락처', validators=[DataRequired()])
    project_type = StringField('유형', validators=[DataRequired()])
    project_id = StringField('프로젝트 ID', validators=[DataRequired()])
    project_url = StringField('프로젝트 관리페이지', validators=[DataRequired(), URL()])
    purpose = TextAreaField('과제목적', validators=[DataRequired()])
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
    # Create message
    msg = MIMEMultipart('alternative')
    msg['Subject'] = 'RTM AI POC 신청 완료 안내'
    msg['From'] = os.getenv('SMTP_FROM')
    msg['To'] = to_email

    # Read template
    with open('templates/online-poc-email-welcome.html', 'r', encoding='utf-8') as f:
        template = Template(f.read())

    # Add timestamp
    data['접수시각'] = datetime.now().strftime('%Y-%m-%d %H:%M')

    # Render template with data
    html_content = template.render(**data)

    # Attach HTML content
    msg.attach(MIMEText(html_content, 'html'))

    # Send email
    smtp = aiosmtplib.SMTP(
        hostname=os.getenv('SMTP_HOST'),
        port=int(os.getenv('SMTP_PORT')),
        use_tls=True
    )

    await smtp.connect()
    await smtp.login(os.getenv('SMTP_USER'), os.getenv('SMTP_PASSWORD'))
    await smtp.send_message(msg)
    await smtp.quit()

async def send_status_email(project, template_name, subject):
    """Send status update email using specified template"""
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
        use_tls=True
    )

    await smtp.connect()
    await smtp.login(os.getenv('SMTP_USER'), os.getenv('SMTP_PASSWORD'))
    await smtp.send_message(msg)
    await smtp.quit()

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
    data = request.json
    try:
        await send_email(data['이메일'], data)
        return jsonify({'status': 'success', 'message': '이메일이 성공적으로 발송되었습니다.'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/project/initial-request', methods=['POST'])
async def initial_request():
    """Handle initial POC request"""
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
    
    await send_status_email(
        project,
        'online-poc-email-welcome',
        'RTM AI POC 신청 완료 안내'
    )
    
    return jsonify({'status': 'success', 'message': '초기 신청이 완료되었습니다.'})

@app.route('/api/project/complete', methods=['POST'])
async def complete_application():
    """Handle POC application completion"""
    data = request.json
    project = Project.query.get(data['프로젝트ID'])
    
    if not project:
        return jsonify({'status': 'error', 'message': '프로젝트를 찾을 수 없습니다.'}), 404
    
    project.status = ProjectStatus.APPLICATION_COMPLETE
    db.session.commit()
    
    await send_status_email(
        project,
        'online-poc-email-complete',
        'RTM AI POC 신청 완료 안내'
    )
    
    return jsonify({'status': 'success', 'message': '신청이 완료되었습니다.'})

@app.route('/api/project/cancel', methods=['POST'])
async def cancel_project():
    """Handle project cancellation"""
    data = request.json
    project = Project.query.get(data['프로젝트ID'])
    
    if not project:
        return jsonify({'status': 'error', 'message': '프로젝트를 찾을 수 없습니다.'}), 404
    
    project.status = ProjectStatus.CANCELLED
    db.session.commit()
    
    await send_status_email(
        project,
        'online-poc-email-cancel',
        'RTM AI POC 신청 취소 안내'
    )
    
    return jsonify({'status': 'success', 'message': '프로젝트가 취소되었습니다.'})

@app.route('/api/project/complete-report', methods=['POST'])
async def send_completion_report():
    """Send completion report"""
    data = request.json
    project = Project.query.get(data['프로젝트ID'])
    
    if not project:
        return jsonify({'status': 'error', 'message': '프로젝트를 찾을 수 없습니다.'}), 404
    
    project.status = ProjectStatus.COMPLETED
    db.session.commit()
    
    await send_status_email(
        project,
        'online-poc-email-report',
        'RTM AI POC 완료 보고서'
    )
    
    return jsonify({'status': 'success', 'message': '완료 보고서가 발송되었습니다.'})

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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 