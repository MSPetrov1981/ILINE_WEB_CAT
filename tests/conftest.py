import sys
import os
import uuid
import pytest
import tempfile
import warnings

from datetime import datetime, date, timedelta
from unittest.mock import Mock, patch

# Подавляем предупреждение об устаревшем utcnow
warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    message="datetime.datetime.utcnow() is deprecated"
)

# Подавляем предупреждение об устаревшем Query.get()
try:
    from sqlalchemy.exc import LegacyAPIWarning
    warnings.filterwarnings(
        "ignore",
        category=LegacyAPIWarning,
        message="The Query.get() method is considered legacy"
    )
except ImportError:
    # Если LegacyAPIWarning не доступен, то игнорируем
    pass

# Добавляем корневую директорию проекта в путь Python
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(project_root, '..'))

try:
    from app import create_app, db
    from app.models import User, Employee, LoginLog
    from app.services.auth_service import AuthService
    from app.services.employee_service import EmployeeService
    from app.services.search_service import SearchService
    from app.services.analytics_service import AnalyticsService
except ImportError as e:
    print(f"Import error: {e}")
    print(f"Current sys.path: {sys.path}")
    raise

@pytest.fixture(scope='session')
def app():
    """Создание тестового приложения Flask"""
    # Создаем временный файл для базы данных
    db_fd, db_path = tempfile.mkstemp()
    
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key'
    })
    
    with app.app_context():
        db.create_all()
    
    yield app
    
    # Очистка после тестов
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    """Тестовый клиент Flask"""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Тестовый runner для CLI команд"""
    return app.test_cli_runner()

@pytest.fixture(scope='function')
def init_database(app):
    """Инициализация тестовой базы данных"""
    with app.app_context():
        # Очищаем базу
        db.drop_all()
        db.create_all()
        
        # Создаем тестового пользователя
        user = User(
            username='testuser',
            email='test@example.com'
        )
        user.set_password('testpassword')
        db.session.add(user)
        
        # Создаем тестовых сотрудников
        employees = [
            Employee(
                full_name='Иван Иванов',
                position='Разработчик',
                hire_date=date(2020, 1, 15),
                salary=100000,
                boss_id=None
            ),
            Employee(
                full_name='Петр Петров',
                position='Менеджер',
                hire_date=date(2021, 5, 20),
                salary=150000,
                boss_id=1
            ),
            Employee(
                full_name='Сидор Сидоров',
                position='Аналитик',
                hire_date=date(2022, 3, 10),
                salary=120000,
                boss_id=2
            ),
            Employee(
                full_name='Анна Аннова',
                position='Разработчик',
                hire_date=date(2023, 8, 5),
                salary=110000,
                boss_id=1
            ),
            Employee(
                full_name='Мария Маринова',
                position='Тестировщик',
                hire_date=date(2024, 1, 10),
                salary=90000,
                boss_id=2
            )
        ]
        
        for emp in employees:
            db.session.add(emp)
        
        db.session.commit()
        
    yield db
    
    with app.app_context():
        db.session.remove()

@pytest.fixture
def auth_service():
    """Сервис аутентификации"""
    return AuthService(log_file='test_auth_logs.csv')

@pytest.fixture
def employee_service():
    """Сервис сотрудников"""
    return EmployeeService()

@pytest.fixture
def search_service():
    """Сервис поиска"""
    return SearchService()

@pytest.fixture
def analytics_service():
    """Сервис аналитики"""
    return AnalyticsService

@pytest.fixture
def auth_headers(app):
    """Заголовки для аутентифицированных запросов"""
    # Вместо использования клиента в фикстуре, просто возвращаем пустой словарь
    # Аутентификацию будем делать в тестах через сессию
    return {}

@pytest.fixture
def authenticated_client(client, app):
    with app.app_context():
        from app import db
        from app.models import User

        unique_id = uuid.uuid4().hex[:8]
        username = f'test_user_{unique_id}'
        email = f'test_{unique_id}@example.com'

        user = User(username=username, email=email)
        user.set_password('testpassword')
        db.session.add(user)
        db.session.commit()

        with client.session_transaction() as session:
            # Попробуем оба варианта, чтобы покрыть разные механизмы аутентификации
            session['user_id'] = user.id
            session['_user_id'] = str(user.id)
            session['_fresh'] = False

        yield client

        db.session.delete(user)
        db.session.commit()


def cleanup_users(app):
    """Автоматически очищает тестовых пользователей после каждого теста"""
    yield
    
    with app.app_context():
        # Удаляем всех пользователей с test_ в имени
        test_users = User.query.filter(User.username.like('test_%')).all()
        for user in test_users:
            db.session.delete(user)
        db.session.commit()

@pytest.fixture
def sample_employee_data():
    """Тестовые данные сотрудника"""
    return {
        'full_name': 'Тест Тестов',
        'position': 'Тестировщик',
        'hire_date': '2024-01-01',
        'salary': 80000,
        'boss_id': 0
    }

@pytest.fixture
def sample_filter_data():
    """Тестовые данные для фильтрации"""
    return {
        'min_salary': 100000,
        'max_salary': 150000,
        'start_date': '2020-01-01',
        'end_date': '2024-12-31'
    }

@pytest.fixture
def mock_request_context(app):
    """Мок контекста запроса"""
    with app.test_request_context():
        yield