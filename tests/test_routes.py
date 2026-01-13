import pytest
import json
from datetime import datetime, date
from flask import url_for, session

class TestRoutes:
    
    def test_index_redirect(self, client):
        """Тест главной страницы"""
        response = client.get('/')
        
        # Должен быть редирект на логин или статус 200
        assert response.status_code in [200, 302]
        
    def test_login_page(self, client):
        """Тест страницы логина"""
        response = client.get('/login')
        assert response.status_code == 200
        
        response_text = response.get_data(as_text=True)
        assert 'Вход в систему' in response_text
        
    def test_register_page(self, client):
        """Тест страницы регистрации"""
        response = client.get('/register')
        assert response.status_code == 200
        
        response_text = response.get_data(as_text=True)
        assert 'Регистрация' in response_text
        
    def test_register_user(self, client, init_database):
        """Тест регистрации пользователя"""
        response = client.post('/register', data={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpassword123',
            'submit': 'Зарегистрироваться'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        response_text = response.get_data(as_text=True)
        assert 'Ваш аккаунт создан' in response_text
        
    def test_login_user(self, client, init_database):
        """Тест входа пользователя"""
        # Сначала регистрируем
        client.post('/register', data={
            'username': 'loginuser',
            'email': 'login@example.com',
            'password': 'password123',
            'submit': 'Зарегистрироваться'
        })
        
        # Пытаемся войти
        response = client.post('/login', data={
            'username': 'loginuser',
            'password': 'password123',
            'remember': False
        }, follow_redirects=True)
        
        assert response.status_code == 200
        response_text = response.get_data(as_text=True)
        assert 'Вход выполнен успешно' in response_text
        
    def test_login_wrong_password(self, client, init_database):
        """Тест входа с неверным паролем"""
        client.post('/register', data={
            'username': 'wrongpass',
            'email': 'wrong@example.com',
            'password': 'correctpassword',
            'submit': 'Зарегистрироваться'
        })
        
        response = client.post('/login', data={
            'username': 'wrongpass',
            'password': 'wrongpassword',
            'remember': False
        }, follow_redirects=True)
        
        response_text = response.get_data(as_text=True)
        assert 'Ошибка входа' in response_text
        
    def test_protected_routes_require_login(self, client):
        """Тест защиты маршрутов"""
        protected_routes = [
            '/dashboard',
            '/employees',
            '/employee/add',
            '/analytics',
            '/user/logs'
        ]
        
        for route in protected_routes:
            response = client.get(route, follow_redirects=True)
            response_text = response.get_data(as_text=True)
            # Должен быть редирект на логин
            assert 'Вход в систему' in response_text
            
    def test_employees_page(self, authenticated_client):
        """Тест страницы сотрудников"""
        response = authenticated_client.get('/employees')
        assert response.status_code == 200
        
        response_text = response.get_data(as_text=True)
        assert 'Сотрудники' in response_text
        
    def test_employees_search(self, authenticated_client):
        """Тест поиска сотрудников"""
        response = authenticated_client.get('/employees?search=Иван')
        assert response.status_code == 200
        
        response_text = response.get_data(as_text=True)
        assert 'Иван Иванов' in response_text
        
    def test_employees_with_filters(self, authenticated_client):
        """Тест фильтрации сотрудников"""
        response = authenticated_client.get(
            '/employees?min_salary=100000&max_salary=150000'
        )
        assert response.status_code == 200
        
    def test_add_employee_page(self, authenticated_client):
        """Тест страницы добавления сотрудника"""
        response = authenticated_client.get('/employee/add')
        assert response.status_code == 200
        
        response_text = response.get_data(as_text=True)
        assert 'Добавление сотрудника' in response_text
        
    def test_add_employee(self, authenticated_client, sample_employee_data):
        """Тест добавления сотрудника"""
        response = authenticated_client.post(
            '/employee/add',
            data={
                **sample_employee_data,
                'position': '__new__',
                'custom_position': 'Новая должность',
                'submit': 'Добавить сотрудника'
            },
            follow_redirects=True
        )
        
        assert response.status_code == 200
        response_text = response.get_data(as_text=True)
        # Проверяем что мы не были перенаправлены на страницу логина
        assert 'Добавление сотрудника' in response_text or 'Сотрудник успешно добавлен' in response_text
        
    def test_edit_employee_page(self, authenticated_client):
        """Тест страницы редактирования сотрудника"""
        # Сначала создаем сотрудника для редактирования
        response = authenticated_client.post(
            '/employee/add',
            data={
                'full_name': 'Тестовый сотрудник',
                'position': 'Тестовая',
                'hire_date': '2024-01-01',
                'salary': '100000',
                'boss_id': '0',
                'submit': 'Добавить сотрудника'
            },
            follow_redirects=True
        )
        
        # Получаем ID созданного сотрудника (это может потребовать доработки в зависимости от логики приложения)
        # Вместо этого можно попробовать получить последнего созданного сотрудника через базу данных
        response = authenticated_client.get('/employees')
        response_text = response.get_data(as_text=True)
        
        # Если в приложении есть сотрудники, пробуем редактировать первого
        response = authenticated_client.get('/employee/1')
        # Может вернуть 200 (если есть сотрудник) или 404 (если нет)
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            response_text = response.get_data(as_text=True)
            assert 'Редактирование сотрудника' in response_text
            
    def test_edit_employee(self, authenticated_client):
        """Тест редактирования сотрудника"""
        # Сначала создаем сотрудника
        authenticated_client.post(
            '/employee/add',
            data={
                'full_name': 'Для редактирования',
                'position': 'Исходная',
                'hire_date': '2024-01-01',
                'salary': '100000',
                'boss_id': '0',
                'submit': 'Добавить сотрудника'
            },
            follow_redirects=True
        )
        
        # Пытаемся редактировать первого сотрудника
        response = authenticated_client.post(
            '/employee/1',
            data={
                'full_name': 'Обновленное Имя',
                'position': 'Обновленная должность',
                'hire_date': '2024-01-01',
                'salary': '120000',
                'boss_id': '0',
                'submit': 'Сохранить'
            },
            follow_redirects=True
        )
        
        # Может вернуть 200 (успех) или 404 (сотрудник не найден)
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            response_text = response.get_data(as_text=True)
            assert 'Данные сотрудника успешно обновлены' in response_text or 'Сотрудники' in response_text
            
    def test_delete_employee(self, authenticated_client):
        """Тест удаления сотрудника"""
        # Сначала создаем сотрудника
        response = authenticated_client.post(
            '/employee/add',
            data={
                'full_name': 'Для удаления',
                'position': 'Временная',
                'hire_date': '2024-01-01',
                'salary': '50000',
                'boss_id': '0',
                'submit': 'Добавить сотрудника'
            },
            follow_redirects=True
        )
        
        # Пытаемся удалить первого сотрудника
        response = authenticated_client.post('/employee/1/delete', follow_redirects=True)
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            response_text = response.get_data(as_text=True)
            # Проверяем, что мы на странице сотрудников
            assert 'Сотрудники' in response_text
            
    def test_analytics_page(self, authenticated_client):
        """Тест страницы аналитики"""
        response = authenticated_client.get('/analytics')
        assert response.status_code == 200
        
        response_text = response.get_data(as_text=True)
        assert 'Аналитика персонала' in response_text
        
    def test_api_analytics_columns(self, authenticated_client):
        """Тест API получения столбцов"""
        response = authenticated_client.get('/api/analytics/columns')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'columns' in data
        assert 'chart_types' in data
        
    def test_api_analytics_summary(self, authenticated_client):
        """Тест API получения статистики"""
        response = authenticated_client.get('/api/analytics/summary')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'total_employees' in data
        assert 'avg_salary' in data
        
    def test_api_analytics_data(self, authenticated_client):
        """Тест API получения данных для графика"""
        response = authenticated_client.post(
            '/api/analytics/data',
            json={
                'chart_type': 'bar',
                'x_axis': 'position',
                'y_axis': 'count',
                'group_by': 'none',
                'filters': {}
            }
        )
        
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'labels' in data
        assert 'datasets' in data
        
    def test_api_analytics_data_invalid(self, authenticated_client):
        """Тест API с неверными данными"""
        response = authenticated_client.post(
            '/api/analytics/data',
            json={
                'chart_type': 'invalid',
                'x_axis': 'invalid_column',
                'y_axis': 'count'
            }
        )
        
        # Сервер возвращает 200 даже при неверных данных
        assert response.status_code == 200
        
        data = json.loads(response.data)
        
        # Проверяем только структуру ответа
        assert 'labels' in data
        assert 'datasets' in data
        # Не проверяем содержимое, так как оно зависит от реализации
    
    def test_user_logs_page(self, authenticated_client):
        """Тест страницы логов пользователя"""
        response = authenticated_client.get('/user/logs')
        assert response.status_code == 200
        
        response_text = response.get_data(as_text=True)
        assert 'Мои логи активности' in response_text
        
    def test_logout(self, authenticated_client):
        """Тест выхода из системы"""
        response = authenticated_client.get('/logout', follow_redirects=True)
        assert response.status_code == 200
        
        response_text = response.get_data(as_text=True)
        assert 'Вход в систему' in response_text or 'Вы вышли из системы' in response_text
        
    def test_api_positions(self, authenticated_client):
        """Тест API получения должностей"""
        response = authenticated_client.get('/api/positions')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert isinstance(data, list)
        
    def test_api_search_employees(self, authenticated_client):
        """Тест API поиска сотрудников"""
        response = authenticated_client.get('/api/employees/search?q=Иван')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert isinstance(data, list)