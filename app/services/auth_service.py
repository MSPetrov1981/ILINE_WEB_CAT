import csv
import os
from datetime import datetime
from app.models import LoginLog, db

class AuthService:
    def __init__(self, log_file='auth_logs.csv'):
        self.log_file = log_file
        self._ensure_log_file()
    
    def _ensure_log_file(self):
        """Создает файл логов если он не существует"""
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'username', 'action', 'ip_address', 'user_agent', 'session_duration'])
    
    def log_auth_event(self, username, action, ip_address=None, user_agent=None, session_duration=None):
        """Логирует события авторизации в CSV файл"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        with open(self.log_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, username, action, ip_address, user_agent, session_duration])
    
    def create_login_log(self, user_id, ip_address=None, user_agent=None):
        """Создает запись о входе в БД"""
        login_log = LoginLog(
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.session.add(login_log)
        db.session.commit()
        return login_log
    
    def update_logout_log(self, login_log_id):
        """Обновляет запись о выходе в БД"""
        login_log = LoginLog.query.get(login_log_id)
        if login_log:
            login_log.logout_time = datetime.utcnow()
            if login_log.login_time:
                login_log.session_duration = (login_log.logout_time - login_log.login_time).total_seconds()
            db.session.commit()
    
    def get_user_logs(self, user_id):
        """Получает логи пользователя"""
        return LoginLog.query.filter_by(user_id=user_id).order_by(LoginLog.login_time.desc()).all()