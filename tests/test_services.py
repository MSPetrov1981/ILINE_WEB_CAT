import pytest
import os
from datetime import datetime, date
from app.services.auth_service import AuthService
from app.services.employee_service import EmployeeService
from app.services.search_service import SearchService
from app.models import User, Employee, LoginLog
from app import db

class TestAuthService:
    
    def test_init_auth_service(self):
        """Тест инициализации AuthService"""
        service = AuthService(log_file='test_auth.csv')
        assert service.log_file == 'test_auth.csv'
        
        # Проверяем, что файл создан
        assert os.path.exists('test_auth.csv')
        
        # Очистка после тестов
        if os.path.exists('test_auth.csv'):
            os.remove('test_auth.csv')
    
    def test_log_auth_event(self, auth_service):
        """Тест логирования события аутентификации"""
        auth_service.log_auth_event(
            username='testuser',
            action='LOGIN',
            ip_address='127.0.0.1',
            user_agent='Test Agent'
        )
        
        # Проверяем, что файл существует и не пустой
        assert os.path.exists(auth_service.log_file)
        assert os.path.getsize(auth_service.log_file) > 0
        
    def test_create_and_update_login_log(self, app, init_database):
        """Тест создания и обновления лога входа"""
        with app.app_context():
            auth_service = AuthService(log_file='test_auth.csv')
            from app.models import User
            
            user = User.query.first()
            
            # Создаем лог входа
            login_log = auth_service.create_login_log(
                user_id=user.id,
                ip_address='127.0.0.1'
            )
            
            assert login_log.id is not None
            assert login_log.user_id == user.id
            assert login_log.ip_address == '127.0.0.1'
            assert login_log.logout_time is None
    
    def test_get_user_logs(self, app, init_database, auth_service):
        """Тест получения логов пользователя"""
        with app.app_context():
            user = User.query.first()
            
            # Создаем несколько логов
            for _ in range(3):
                auth_service.create_login_log(user.id)
            
            logs = auth_service.get_user_logs(user.id)
            assert len(logs) == 3
            assert all(log.user_id == user.id for log in logs)

class TestEmployeeService:
    
    def test_get_all_employees(self, app, init_database, employee_service):
        """Тест получения всех сотрудников"""
        with app.app_context():
            result = employee_service.get_all_employees(page=1, per_page=2)
            
            assert hasattr(result, 'items')
            assert hasattr(result, 'total')
            assert len(result.items) == 2
            assert result.total == 5
    
    def test_get_employee_by_id(self, app, init_database, employee_service):
        """Тест получения сотрудника по ID"""
        with app.app_context():
            employee = employee_service.get_employee_by_id(1)
            
            assert employee is not None
            assert employee.id == 1
            assert employee.full_name == 'Иван Иванов'
    
    def test_get_nonexistent_employee(self, app, init_database, employee_service):
        """Тест получения несуществующего сотрудника"""
        with app.app_context():
            employee = employee_service.get_employee_by_id(999)
            assert employee is None
    
    def test_create_employee(self, app, init_database, employee_service, sample_employee_data):
        """Тест создания сотрудника"""
        with app.app_context():
            employee_data = sample_employee_data.copy()
            employee_data['hire_date'] = date.fromisoformat(employee_data['hire_date'])
            employee_data['boss_id'] = None if employee_data['boss_id'] == 0 else employee_data['boss_id']
            
            employee = employee_service.create_employee(**employee_data)
            
            assert employee.id is not None
            assert employee.full_name == 'Тест Тестов'
            assert employee.position == 'Тестировщик'
            assert employee.salary == 80000
            
            # Проверяем, что сотрудник добавлен в базу
            all_employees = employee_service.get_all_employees()
            assert any(e.full_name == 'Тест Тестов' for e in all_employees.items)
    
    def test_update_employee(self, app, init_database, employee_service):
        """Тест обновления сотрудника"""
        with app.app_context():
            updates = {
                'full_name': 'Иван Иванов (обновленный)',
                'salary': 120000,
                'position': 'Старший разработчик'
            }
            
            employee = employee_service.update_employee(1, **updates)
            
            assert employee is not None
            assert employee.full_name == 'Иван Иванов (обновленный)'
            assert employee.salary == 120000
            assert employee.position == 'Старший разработчик'
    
    def test_delete_employee(self, app, init_database, employee_service):
        """Тест удаления сотрудника"""
        with app.app_context():
            # Сначала создаем сотрудника для удаления
            employee = employee_service.create_employee(
                full_name='Для удаления',
                position='Временная',
                hire_date=date.today(),
                salary=50000,
                boss_id=None
            )
            
            employee_id = employee.id
            
            # Удаляем
            result = employee_service.delete_employee(employee_id)
            
            assert result is True
            
            # Проверяем, что сотрудник удален
            deleted_employee = employee_service.get_employee_by_id(employee_id)
            assert deleted_employee is None
    
    def test_delete_employee_with_subordinates(self, app, init_database, employee_service):
        """Тест удаления руководителя с подчиненными"""
        with app.app_context():
            # Создаем руководителя с подчиненными
            boss = employee_service.create_employee(
                full_name='Руководитель',
                position='Директор',
                hire_date=date.today(),
                salary=200000,
                boss_id=None
            )
            
            # Создаем подчиненного
            subordinate = employee_service.create_employee(
                full_name='Подчиненный',
                position='Менеджер',
                hire_date=date.today(),
                salary=100000,
                boss_id=boss.id
            )
            
            # Удаляем руководителя
            result = employee_service.delete_employee(boss.id)
            
            assert result is True
            
            # Проверяем, что подчиненному сбросился boss_id
            updated_subordinate = employee_service.get_employee_by_id(subordinate.id)
            assert updated_subordinate.boss_id is None

class TestSearchService:
    
    def test_search_employees(self, app, init_database, search_service):
        """Тест поиска сотрудников"""
        with app.app_context():
            result = search_service.search_employees('Иван', page=1, per_page=10)
            
            assert result.total == 1
            assert result.items[0].full_name == 'Иван Иванов'
    
    def test_search_by_position(self, app, init_database, search_service):
        """Тест поиска по должности"""
        with app.app_context():
            result = search_service.search_employees('Разработчик', page=1, per_page=10)
            
            assert result.total == 2
            assert all('Разработчик' in emp.position for emp in result.items)
    
    def test_search_empty_query(self, app, init_database, search_service):
        """Тест поиска с пустым запросом"""
        with app.app_context():
            result = search_service.search_employees('', page=1, per_page=10)
            
            assert result.total == 5  # Все сотрудники
    
    def test_search_with_filters(self, app, init_database, search_service):
        """Тест поиска с фильтрами"""
        with app.app_context():
            result = search_service.search_employees(
                query='',
                page=1,
                per_page=10,
                min_salary=120000,
                max_salary=160000
            )
            
            # Должны найти сотрудников с зарплатой 120000-160000
            assert result.total >= 2
            assert all(120000 <= emp.salary <= 160000 for emp in result.items)
    
    def test_search_with_date_filters(self, app, init_database, search_service):
        """Тест поиска с фильтрами по дате"""
        with app.app_context():
            result = search_service.search_employees(
                query='',
                page=1,
                per_page=10,
                start_date=date(2022, 1, 1),
                end_date=date(2024, 12, 31)
            )
            
            # Должны найти сотрудников принятых после 2022 года
            assert result.total >= 3
            assert all(emp.hire_date >= date(2022, 1, 1) for emp in result.items)
    
    def test_get_sorted_employees(self, app, init_database, search_service):
        """Тест получения отсортированных сотрудников"""
        with app.app_context():
            # Сортировка по зарплате по убыванию
            result = search_service.get_sorted_employees(
                sort_by='salary',
                sort_order='desc',
                page=1,
                per_page=10
            )
            
            assert result.total == 5
            # Проверяем сортировку
            salaries = [emp.salary for emp in result.items]
            assert salaries == sorted(salaries, reverse=True)
            
            # Сортировка по дате приема по возрастанию
            result = search_service.get_sorted_employees(
                sort_by='hire_date',
                sort_order='asc',
                page=1,
                per_page=10
            )
            
            dates = [emp.hire_date for emp in result.items]
            assert dates == sorted(dates)
    
    def test_pagination(self, app, init_database, search_service):
        """Тест пагинации"""
        with app.app_context():
            # Первая страница
            page1 = search_service.search_employees('', page=1, per_page=2)
            assert len(page1.items) == 2
            
            # Вторая страница
            page2 = search_service.search_employees('', page=2, per_page=2)
            assert len(page2.items) == 2
            
            # Третья страница
            page3 = search_service.search_employees('', page=3, per_page=2)
            assert len(page3.items) == 1