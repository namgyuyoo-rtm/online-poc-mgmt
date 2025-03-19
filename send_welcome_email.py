import os
import json
from datetime import datetime
from jinja2 import Template
from dotenv import load_dotenv
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import webbrowser
import tempfile

# Load environment variables
load_dotenv()

def parse_request_data(request_text):
    """Parse the request text into a dictionary"""
    lines = request_text.strip().split('\n')
    data = {}
    
    for line in lines:
        if ':' in line:
            key, value = line.split(':', 1)
            data[key.strip()] = value.strip()
    
    # Convert timestamp to formatted string
    if '접수시각' in data:
        try:
            dt = datetime.fromisoformat(data['접수시각'].replace('Z', '+00:00'))
            data['접수시각'] = dt.strftime('%Y-%m-%d %H:%M')
        except:
            pass
    
    return data

def generate_html_preview(data):
    """Generate HTML preview and save to temporary file"""
    # Read template
    with open('online-poc-email-welcome.html', 'r', encoding='utf-8') as f:
        template = Template(f.read())

    # Render template with data
    html_content = template.render(**data)
    
    # Create temporary file
    temp_dir = tempfile.gettempdir()
    preview_file = os.path.join(temp_dir, 'poc_welcome_preview.html')
    
    # Save HTML content
    with open(preview_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return preview_file

def preview_html(file_path):
    """Open HTML preview in default browser"""
    webbrowser.open('file://' + file_path)

def send_email(to_email, data):
    """Send email using SMTP"""
    # Create message
    msg = MIMEMultipart('alternative')
    msg['Subject'] = 'RTM AI POC 신청 완료 안내'
    msg['From'] = os.getenv('SMTP_FROM')
    msg['To'] = to_email

    # Read template
    with open('online-poc-email-welcome.html', 'r', encoding='utf-8') as f:
        template = Template(f.read())

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

    async def send():
        await smtp.connect()
        await smtp.login(os.getenv('SMTP_USER'), os.getenv('SMTP_PASSWORD'))
        await smtp.send_message(msg)
        await smtp.quit()

    import asyncio
    asyncio.run(send())

def main():
    # Example request text
    request_text = """
    :로켓: POC 시작하기 요청
    접수시각: 2025-03-18T23:50:31.523Z
    이름
    테스트7
    회사명
    알티엠
    이메일
    test@rtm.ai
    연락처
    01001010101
    과제목적
    (비활성화)
    유형
    image
    프로젝트ID
    0b0fad21-9b87-4438-8bc1-79c062b927f8
    프로젝트관리페이지
    https://poc-request.hubble-engine.rtm.ai/project/auth
    """

    # Parse request data
    data = parse_request_data(request_text)
    
    # Generate and preview HTML
    print("이메일 미리보기를 생성합니다...")
    preview_file = generate_html_preview(data)
    print(f"미리보기가 생성되었습니다. 브라우저에서 확인해주세요.")
    preview_html(preview_file)
    
    # Ask for confirmation
    response = input("\n이메일을 발송하시겠습니까? (y/n): ")
    if response.lower() == 'y':
        print("이메일을 발송합니다...")
        send_email(data['이메일'], data)
        print("이메일이 성공적으로 발송되었습니다.")
    else:
        print("이메일 발송이 취소되었습니다.")

if __name__ == "__main__":
    main() 