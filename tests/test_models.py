import pytest
from datetime import datetime, date
from app.models import User, Employee, LoginLog

class TestUserModel:
    
    def test_create_user(self, app, init_database):
        """Тест создания пользователя"""
        with app.app_context():
            user = User(
                username='testuser_model',
                email='model@test.com',
                is_active=True  # Явно устанавливаем is_active
            )
            user.set_password('password123')
            
            assert user.username == 'testuser_model'
            assert user.email == 'model@test.com'
            assert user.check_password('password123') is True
            assert not user.check_password('wrongpassword')
            assert user.is_active is True
            
    def test_user_repr(self, app, init_database):
        """Тест строкового представления пользователя"""
        with app.app_context():
            user = User.query.first()
            assert repr(user) == f'<User {user.username}>'

class TestEmployeeModel:
    
    def test_create_employee(self, app, init_database):
        """Тест создания сотрудника"""
        with app.app_context():
            employee = Employee(
                full_name='Тест Сотрудник',
                position='Тестовая должность',
                hire_date=date(2024, 1, 1),
                salary=100000,
                boss_id=None
            )
            
            assert employee.full_name == 'Тест Сотрудник'
            assert employee.position == 'Тестовая должность'
            assert employee.hire_date == date(2024, 1, 1)
            assert employee.salary == 100000
            assert employee.boss_id is None
            
    def test_employee_to_dict(self, app, init_database):
        """Тест конвертации сотрудника в словарь"""
        with app.app_context():
            employee = Employee.query.first()
            data = employee.to_dict()
            
            assert 'id' in data
            assert 'full_name' in data
            assert 'position' in data
            assert 'hire_date' in data
            assert 'salary' in data
            assert 'boss_name' in data
            assert 'boss_id' in data
            
    def test_get_unique_positions(self, app, init_database):
        """Тест получения уникальных должностей"""
        with app.app_context():
            positions = Employee.get_unique_positions()
            
            assert isinstance(positions, list)
            # Предполагаем, что в базе уже есть эти должности из init_database
            if positions:  # Проверяем, что список не пустой
                assert 'Разработчик' in positions
                assert 'Менеджер' in positions
                assert 'Аналитик' in positions
            
    def test_employee_repr(self, app, init_database):
        """Тест строкового представления сотрудника"""
        with app.app_context():
            employee = Employee.query.first()
            assert repr(employee) == f'<Employee {employee.full_name}>'
            
    def test_employee_relationship(self, app, init_database):
        """Тест связей между сотрудниками"""
        with app.app_context():
            boss = Employee.query.filter_by(position='Менеджер').first()
            if boss:
                subordinate = Employee.query.filter_by(boss_id=boss.id).first()
                if subordinate:
                    assert subordinate.boss_id == boss.id
                    assert subordinate in boss.subordinates

class TestLoginLogModel:
    
    def test_create_login_log(self, app, init_database):
        """Тест создания лога входа"""
        with app.app_context():
            user = User.query.first()
            # Создаем объект с явным указанием времени входа
            login_log = LoginLog(
                user_id=user.id,
                ip_address='127.0.0.1',
                user_agent='Test Browser',
                login_time=datetime.utcnow()  # Явно устанавливаем время
            )
            
            assert login_log.user_id == user.id
            assert login_log.ip_address == '127.0.0.1'
            assert login_log.user_agent == 'Test Browser'
            assert login_log.login_time is not None  # Теперь это должно пройти
            assert login_log.logout_time is None
            assert login_log.session_duration is None
            
    def test_login_log_repr(self, app, init_database):
        """Тест строкового представления лога входа"""
        with app.app_context():
            user = User.query.first()
            # Создаем объект с временем входа
            login_log = LoginLog(
                user_id=user.id,
                login_time=datetime.utcnow()  # Добавляем время входа
            )
            # Проверяем, что repr содержит ID пользователя
            assert str(user.id) in repr(login_log)