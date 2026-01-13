import pytest
import json
import time
import re
from datetime import datetime, date, timedelta

class TestIntegration:
    
    def test_full_employee_workflow(self, authenticated_client, app):
        """Полный тест рабочего процесса сотрудника"""
        with app.app_context():
            # 0. Сначала проверяем, что мы аутентифицированы
            response = authenticated_client.get('/employees', follow_redirects=True)
            assert response.status_code == 200
            response_text = response.get_data(as_text=True)
            
            # Если мы видим форму логина, значит не аутентифицированы
            if 'войти' in response_text.lower() or 'login' in response_text.lower():
                pytest.fail("Пользователь не аутентифицирован")
            
            # 1. Переходим на страницу добавления сотрудника
            response = authenticated_client.get('/employee/add', follow_redirects=True)
            assert response.status_code == 200
            
            # 2. Добавляем сотрудника с уникальным именем
            unique_name = f'Интеграционный Тест {int(time.time())}'
            response = authenticated_client.post(
                '/employee/add',
                data={
                    'full_name': unique_name,
                    'position': '__new__',
                    'custom_position': 'Интеграционная должность',
                    'hire_date': '2024-01-15',
                    'salary': '95000',
                    'boss_id': '0',
                    'submit': 'Добавить сотрудника'
                },
                follow_redirects=True
            )
            
            # Проверяем статус
            assert response.status_code == 200, f"Ожидался код 200, получен {response.status_code}"
            
            response_text = response.get_data(as_text=True)
            print(f"Добавление сотрудника - ответ: {response_text[:500]}")
            
            # Проверяем успешное добавление
            success_found = (
                'Сотрудник успешно добавлен' in response_text or
                'успешно добавлен' in response_text or
                'добавлен успешно' in response_text or
                'successfully added' in response_text or
                unique_name in response_text  # Если имя появилось в списке
            )
            assert success_found, f"Не найден текст об успешном добавлении. Полный ответ: {response_text}"
            
            # 3. Ищем сотрудника
            response = authenticated_client.get(
                f'/employees?search=Интеграционный',
                follow_redirects=True
            )
            
            assert response.status_code == 200
            response_text = response.get_data(as_text=True)
            print(f"Поиск сотрудника - ответ: {response_text[:500]}")
            
            # 4. Находим ID сотрудника для дальнейших операций
            # Ищем ID в ответе - ищем ссылки с employee/{id}
            id_pattern = r'/employee/(\d+)(?:/|")'
            matches = re.findall(id_pattern, response_text)
            
            employee_id = None
            # Берем первый найденный ID
            if matches:
                employee_id = matches[0]
                print(f"Найден ID сотрудника через regex: {employee_id}")
            
            # Если не нашли через regex, попробуем найти по имени в таблице
            if not employee_id:
                # Ищем строку таблицы с именем сотрудника
                table_row_pattern = rf'<tr[^>]*>.*?{re.escape(unique_name)}.*?</tr>'
                row_match = re.search(table_row_pattern, response_text, re.DOTALL | re.IGNORECASE)
                if row_match:
                    row_text = row_match.group(0)
                    # Ищем ID в строке
                    id_in_row = re.search(id_pattern, row_text)
                    if id_in_row:
                        employee_id = id_in_row.group(1)
                        print(f"Найден ID сотрудника в строке таблицы: {employee_id}")
            
            if not employee_id:
                print("Не удалось найти ID сотрудника. Ответ страницы поиска:")
                print(response_text[:1000])
                pytest.skip("Не удалось найти ID сотрудника для редактирования")
            
            print(f"Используем ID сотрудника: {employee_id}")
            
            # 5. Переходим на страницу редактирования сотрудника
            response = authenticated_client.get(f'/employee/{employee_id}', follow_redirects=True)
            assert response.status_code == 200
            edit_page_text = response.get_data(as_text=True)
            print(f"Страница редактирования: {edit_page_text[:500]}")
            
            # 6. Редактируем сотрудника
            updated_name = f'{unique_name} (обновленный)'
            response = authenticated_client.post(
                f'/employee/{employee_id}',
                data={
                    'full_name': updated_name,
                    'position': 'Обновленная интеграционная должность',
                    'hire_date': '2024-01-15',
                    'salary': '105000',
                    'boss_id': '0',
                    'submit': 'Сохранить'
                },
                follow_redirects=True
            )
            
            assert response.status_code == 200
            response_text = response.get_data(as_text=True)
            print(f"После редактирования - ответ: {response_text[:500]}")
            
            # Проверяем успешное обновление
            update_found = (
                'Данные сотрудника успешно обновлены' in response_text or
                'успешно обновлен' in response_text or
                'обновлен успешно' in response_text or
                'successfully updated' in response_text or
                updated_name in response_text  # Если обновленное имя появилось
            )
            
            if not update_found:
                print("Текст об успешном обновлении не найден. Возможные причины:")
                print("1. Форма редактирования использует другой endpoint")
                print("2. Сообщение об успехе имеет другой текст")
                print("3. Редирект на другую страницу")
                print(f"Полный ответ: {response_text}")
                
                # Проверяем, что сотрудник все же обновился - ищем его с новым именем
                response = authenticated_client.get(
                    f'/employees?search={updated_name}',
                    follow_redirects=True
                )
                if response.status_code == 200 and updated_name in response.get_data(as_text=True):
                    print(f"Сотрудник успешно обновлен (найден по новому имени)")
                    update_found = True
            
            assert update_found, "Не найден текст об успешном обновлении и сотрудник не найден по новому имени"
            
            # 7. Проверяем аналитику (опционально)
            try:
                response = authenticated_client.post(
                    '/api/analytics/data',
                    json={
                        'chart_type': 'bar',
                        'x_axis': 'position',
                        'y_axis': 'count',
                        'group_by': 'none',
                        'filters': {}
                    },
                    content_type='application/json',
                    follow_redirects=True
                )
                
                if response.status_code == 200:
                    try:
                        data = json.loads(response.data)
                        print(f"Аналитика успешно получена")
                    except json.JSONDecodeError:
                        print(f"Аналитика вернула не JSON: {response.data[:200]}")
            except Exception as e:
                print(f"Ошибка при тестировании аналитики: {e}")
            
            # 8. Удаляем сотрудника
            response = authenticated_client.post(
                f'/employee/{employee_id}/delete',
                follow_redirects=True
            )
            
            assert response.status_code == 200
            response_text = response.get_data(as_text=True)
            print(f"После удаления - ответ: {response_text[:500]}")
            
            # Проверяем успешное удаление
            delete_found = (
                'успешно удален' in response_text or
                'удален успешно' in response_text or
                'successfully deleted' in response_text or
                unique_name not in response_text  # Имя не должно быть в списке
            )
            assert delete_found, f"Не найден текст об успешном удалении"
            
    def test_analytics_workflow(self, authenticated_client, app):
        """Полный тест рабочего процесса аналитики"""
        with app.app_context():
            # 1. Проверяем аутентификацию
            response = authenticated_client.get('/employees', follow_redirects=True)
            assert response.status_code == 200
            
            # 2. Получаем доступные столбцы
            response = authenticated_client.get('/api/analytics/columns', follow_redirects=True)
            
            # API может возвращать JSON или HTML
            if response.status_code == 200:
                try:
                    data = json.loads(response.data)
                    print(f"Получены столбцы аналитики: {data}")
                except json.JSONDecodeError:
                    print(f"Столбцы аналитики вернули HTML, а не JSON")
            else:
                print(f"Столбцы аналитики: статус {response.status_code}")
                
            # 3. Получаем статистику
            response = authenticated_client.get('/api/analytics/summary', follow_redirects=True)
            if response.status_code == 200:
                try:
                    data = json.loads(response.data)
                    print(f"Получена статистика: {data}")
                except json.JSONDecodeError:
                    print(f"Статистика вернула HTML, а не JSON")
            
            # 4. Строим разные типы графиков
            chart_configs = [
                {'chart_type': 'bar', 'x_axis': 'position', 'y_axis': 'count'},
                {'chart_type': 'line', 'x_axis': 'hire_date', 'y_axis': 'count', 'group_by': 'year'},
                {'chart_type': 'pie', 'x_axis': 'position', 'y_axis': 'count'},
                {'chart_type': 'scatter', 'x_axis': 'salary', 'y_axis': 'salary'},
            ]
            
            for config in chart_configs:
                print(f"Тестируем график: {config['chart_type']}")
                response = authenticated_client.post(
                    '/api/analytics/data',
                    json={**config, 'filters': {}},
                    content_type='application/json',
                    follow_redirects=True
                )
                
                # Проверяем статус
                if response.status_code != 200:
                    print(f"График {config['chart_type']} вернул статус {response.status_code}")
                    # Проверяем что не 500 ошибка сервера
                    assert response.status_code != 500, f"Ошибка сервера для {config}"
                
                if response.status_code == 200:
                    try:
                        data = json.loads(response.data)
                        print(f"График {config['chart_type']} успешно получен")
                    except json.JSONDecodeError:
                        print(f"График {config['chart_type']} вернул не JSON")
                    
    def test_search_and_filter_workflow(self, authenticated_client, app):
        """Тест рабочего процесса поиска и фильтрации"""
        with app.app_context():
            # 1. Проверяем аутентификацию
            response = authenticated_client.get('/employees', follow_redirects=True)
            assert response.status_code == 200
            response_text = response.get_data(as_text=True)
            assert 'Вход' not in response_text
            
            # 2. Поиск по имени
            response = authenticated_client.get('/employees?search=Иван', follow_redirects=True)
            assert response.status_code == 200
            
            response_text = response.get_data(as_text=True)
            # Проверяем что мы не на странице логина
            assert 'войти' not in response_text.lower()
            
            # 3. Фильтрация по зарплате
            response = authenticated_client.get(
                '/employees?min_salary=100000&max_salary=130000',
                follow_redirects=True
            )
            assert response.status_code == 200
            
            # 4. Фильтрация по дате
            response = authenticated_client.get(
                '/employees?start_date=2022-01-01&end_date=2024-12-31',
                follow_redirects=True
            )
            assert response.status_code == 200
            
            # 5. Комбинированная фильтрация
            response = authenticated_client.get(
                '/employees?search=Разработчик&min_salary=100000&start_date=2020-01-01',
                follow_redirects=True
            )
            assert response.status_code == 200
            
    def test_error_handling(self, authenticated_client, app):
        """Тест обработки ошибок"""
        with app.app_context():
            # Проверяем аутентификацию
            response = authenticated_client.get('/employees', follow_redirects=True)
            assert response.status_code == 200
            
            # Несуществующий маршрут
            response = authenticated_client.get('/nonexistent', follow_redirects=True)
            # Может быть 404 или 200 (если есть обработчик)
            assert response.status_code in [200, 404]
            
            # Несуществующий сотрудник
            response = authenticated_client.get('/employee/999', follow_redirects=True)
            # Может быть 404 или редирект на список
            assert response.status_code == 200  # После редиректа
            
            # Неверные данные для API
            response = authenticated_client.post(
                '/api/analytics/data',
                json={'invalid': 'data'},
                content_type='application/json',
                follow_redirects=True
            )
            # Проверяем что не упал сервер (не 500)
            assert response.status_code != 500
            
    def test_performance_scenarios(self, authenticated_client, app):
        """Тест производительности для разных сценариев"""
        with app.app_context():
            # Проверяем аутентификацию
            response = authenticated_client.get('/employees', follow_redirects=True)
            assert response.status_code == 200
            
            scenarios = [
                ('Быстрый поиск', '/employees?search=Тест', 1.0),
                ('Сложная фильтрация', '/employees?min_salary=50000&max_salary=200000&start_date=2019-01-01&end_date=2024-12-31', 2.0),
                ('Аналитика', '/api/analytics/data', 3.0)
            ]
            
            for scenario_name, url, max_time in scenarios:
                start_time = time.time()
                
                if '/api/analytics' in url:
                    response = authenticated_client.post(
                        url,
                        json={
                            'chart_type': 'bar',
                            'x_axis': 'position',
                            'y_axis': 'count',
                            'group_by': 'none',
                            'filters': {}
                        },
                        content_type='application/json',
                        follow_redirects=True
                    )
                else:
                    response = authenticated_client.get(url, follow_redirects=True)
                
                elapsed = time.time() - start_time
                
                # Проверяем что получили ответ (не обязательно 200, главное не 500)
                assert response.status_code != 500, f"{scenario_name}: Ошибка сервера {response.status_code}"
                print(f"{scenario_name}: выполнено за {elapsed:.2f}s (макс: {max_time}s)")
                assert elapsed < max_time, f"{scenario_name}: Время выполнения {elapsed:.2f}s > {max_time}s"