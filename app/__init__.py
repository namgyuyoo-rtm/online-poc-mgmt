from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
from .models import db
import logging
import os

# 전역 Mail 객체 생성
mail = Mail()

def create_app():
    app = Flask(__name__)
    
    # 로깅 설정
    logging.basicConfig(level=logging.INFO)
    
    # 설정
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///poc.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 이메일 설정
    app.config['MAIL_SERVER'] = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.environ.get('SMTP_PORT', 465))
    app.config['MAIL_USERNAME'] = os.environ.get('SMTP_USER')
    app.config['MAIL_PASSWORD'] = os.environ.get('SMTP_PASSWORD')
    app.config['MAIL_USE_TLS'] = False
    app.config['MAIL_USE_SSL'] = os.environ.get('SMTP_SECURE', 'true').lower() == 'true'
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('SMTP_FROM', 'namgyuyoo@rtm.ai')
    
    # 데이터베이스 초기화
    db.init_app(app)
    
    # Mail 초기화
    mail.init_app(app)
    
    # Migrate 초기화
    migrate = Migrate(app, db)
    
    # 블루프린트 등록
    from .routes import bp
    app.register_blueprint(bp)
    
    # 애플리케이션 컨텍스트 내에서 데이터베이스 테이블 생성
    with app.app_context():
        db.create_all()
    
    return app 