from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from .models import db
import logging
import os

def create_app():
    app = Flask(__name__)
    
    # 로깅 설정
    logging.basicConfig(level=logging.INFO)
    
    # 설정
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///poc.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 데이터베이스 초기화
    db.init_app(app)
    
    # Migrate 초기화
    migrate = Migrate(app, db)
    
    # 블루프린트 등록
    from .routes import bp
    app.register_blueprint(bp)
    
    # 애플리케이션 컨텍스트 내에서 데이터베이스 테이블 생성
    with app.app_context():
        db.create_all()
    
    return app 