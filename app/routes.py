from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, session
from flask_login import login_user, logout_user, current_user, login_required
from app.forms import LoginForm, RegistrationForm, EmployeeForm
from app.models import User, Employee, LoginLog
from app.services.auth_service import AuthService
from app.services.employee_service import EmployeeService
from app.services.search_service import SearchService
from app import db
from datetime import datetime
import sqlalchemy.exc as sql_exc

main = Blueprint('main', __name__)

employee_service = EmployeeService()
search_service = SearchService()
auth_service = AuthService()

@main.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')

@main.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)

@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        try:
            user = User.query.filter_by(username=form.username.data).first()
            
            if user and user.check_password(form.password.data) and user.is_active:
                # Логируем вход
                login_log = auth_service.create_login_log(
                    user.id,
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent')
                )
                
                login_user(user, remember=form.remember.data)
                
                # Сохраняем ID лога в сессии для обновления при выходе
                session['login_log_id'] = login_log.id
                
                # Логируем в файл
                auth_service.log_auth_event(
                    user.username, 
                    'LOGIN', 
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent')
                )
                
                flash('Вход выполнен успешно!', 'success')
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
            else:
                auth_service.log_auth_event(
                    form.username.data, 
                    'FAILED_LOGIN',
                    ip_address=request.remote_addr
                )
                flash('Ошибка входа. Пожалуйста, проверьте имя пользователя и пароль', 'error')
        except Exception as e:
            flash('Ошибка базы данных. Пожалуйста, попробуйте снова.', 'error')
            print(f"Login error: {e}")
    
    return render_template('login.html', form=form)

@main.route('/logout')
@login_required
def logout():
    try:
        # Обновляем лог выхода
        login_log_id = session.get('login_log_id')
        if login_log_id:
            auth_service.update_logout_log(login_log_id)
        
        # Логируем в файл
        if current_user.is_authenticated:
            auth_service.log_auth_event(
                current_user.username, 
                'LOGOUT',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
    except Exception as e:
        print(f"Logout error: {e}")
    
    logout_user()
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('main.index'))

@main.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            user = User(
                username=form.username.data,
                email=form.email.data
            )
            user.set_password(form.password.data)
            
            db.session.add(user)
            db.session.commit()
            
            auth_service.log_auth_event(user.username, 'REGISTER')
            flash('Ваш аккаунт создан! Теперь вы можете войти.', 'success')
            return redirect(url_for('main.login'))
        except sql_exc.IntegrityError:
            db.session.rollback()
            flash('Имя пользователя или email уже существуют.', 'error')
        except Exception as e:
            db.session.rollback()
            flash('Произошла ошибка при регистрации. Пожалуйста, попробуйте снова.', 'error')
            print(f"Registration error: {e}")
    
    return render_template('register.html', form=form)

@main.route('/employees')
@login_required
def employees():
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '')
    sort_by = request.args.get('sort_by', 'id')
    sort_order = request.args.get('sort_order', 'asc')
    
    # Получаем параметры фильтрации по зарплате
    min_salary = request.args.get('min_salary', type=int)
    max_salary = request.args.get('max_salary', type=int)
    
    # Получаем параметры фильтрации по дате приема
    start_date_str = request.args.get('start_date', '')
    end_date_str = request.args.get('end_date', '')
    
    # Конвертируем строки в даты
    start_date = None
    end_date = None
    
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Неверный формат начальной даты', 'error')
            start_date_str = ''
    
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Неверный формат конечной даты', 'error')
            end_date_str = ''
    
    # Валидация: начальная дата не может быть больше конечной
    if start_date and end_date and start_date > end_date:
        flash('Начальная дата не может быть больше конечной', 'error')
        start_date, end_date = end_date, start_date
        start_date_str, end_date_str = end_date_str, start_date_str
    
    # Валидация: минимальная зарплата не может быть больше максимальной
    if min_salary and max_salary and min_salary > max_salary:
        flash('Минимальная зарплата не может быть больше максимальной', 'error')
        min_salary, max_salary = max_salary, min_salary
    
    try:
        if search_query:
            pagination = search_service.search_employees(
                search_query, page, 20, 
                min_salary=min_salary, 
                max_salary=max_salary,
                start_date=start_date,
                end_date=end_date
            )
        else:
            pagination = search_service.get_sorted_employees(
                sort_by, sort_order, page, 20,
                min_salary=min_salary,
                max_salary=max_salary,
                start_date=start_date,
                end_date=end_date
            )
        
        employees = pagination.items
        
        # Передаем текущую дату для вычислений в шаблоне
        now = datetime.now()
        
        return render_template(
            'employees.html',
            employees=employees,
            pagination=pagination,
            search_query=search_query,
            sort_by=sort_by,
            sort_order=sort_order,
            min_salary=min_salary,
            max_salary=max_salary,
            start_date=start_date_str,
            end_date=end_date_str,
            now=now
        )
    except Exception as e:
        flash(f'Ошибка загрузки сотрудников: {str(e)}', 'error')
        return render_template('employees.html', employees=[])

@main.route('/employee/add', methods=['GET', 'POST'])
@login_required
def add_employee():
    form = EmployeeForm()
    
    # Заполняем выпадающий список руководителей
    bosses = Employee.query.all()
    form.boss_id.choices = [(0, 'Нет руководителя')] + [(boss.id, f"{boss.full_name} ({boss.position})") for boss in bosses]
    
    if form.validate_on_submit():
        try:
            boss_id = form.boss_id.data if form.boss_id.data != 0 else None
            
            # Обрабатываем выбор "Добавить новую должность"
            position = form.position.data
            if position == '__new__':
                custom_position = request.form.get('custom_position', '').strip()
                if not custom_position:
                    flash('Пожалуйста, введите название новой должности', 'error')
                    return render_template('add_employee.html', form=form)
                position = custom_position
            
            employee_service.create_employee(
                full_name=form.full_name.data,
                position=position,
                hire_date=form.hire_date.data,
                salary=form.salary.data,
                boss_id=boss_id
            )
            
            auth_service.log_auth_event(
                current_user.username,
                'ADD_EMPLOYEE',
                session_duration=f"Added employee: {form.full_name.data}"
            )
            
            flash('Сотрудник успешно добавлен!', 'success')
            return redirect(url_for('main.employees'))
        except Exception as e:
            flash(f'Ошибка при добавлении сотрудника: {str(e)}', 'error')
    
    return render_template('add_employee.html', form=form)

@main.route('/employee/<int:employee_id>', methods=['GET', 'POST'])
@login_required
def edit_employee(employee_id):
    employee = employee_service.get_employee_by_id(employee_id)
    if not employee:
        flash('Сотрудник не найден', 'error')
        return redirect(url_for('main.employees'))
    
    form = EmployeeForm()
    
    # Заполняем выпадающий список руководителей (исключая текущего сотрудника)
    bosses = Employee.query.filter(Employee.id != employee_id).all()
    form.boss_id.choices = [(0, 'Нет руководителя')] + [(boss.id, f"{boss.full_name} ({boss.position})") for boss in bosses]
    
    if request.method == 'GET':
        form.full_name.data = employee.full_name
        form.position.data = employee.position
        form.hire_date.data = employee.hire_date
        form.salary.data = employee.salary
        form.boss_id.data = employee.boss_id if employee.boss_id else 0
    
    if form.validate_on_submit():
        try:
            boss_id = form.boss_id.data if form.boss_id.data != 0 else None
            
            # Обрабатываем выбор "Добавить новую должность"
            position = form.position.data
            if position == '__new__':
                custom_position = request.form.get('custom_position', '').strip()
                if not custom_position:
                    flash('Пожалуйста, введите название новой должности', 'error')
                    return render_template('edit_employee.html', form=form, employee=employee)
                position = custom_position
            
            employee_service.update_employee(
                employee_id,
                full_name=form.full_name.data,
                position=position,
                hire_date=form.hire_date.data,
                salary=form.salary.data,
                boss_id=boss_id
            )
            
            auth_service.log_auth_event(
                current_user.username,
                'UPDATE_EMPLOYEE',
                session_duration=f"Updated employee: {employee_id}"
            )
            
            flash('Данные сотрудника успешно обновлены', 'success')
            return redirect(url_for('main.employees'))
        except Exception as e:
            flash(f'Ошибка обновления сотрудника: {str(e)}', 'error')
    
    return render_template('edit_employee.html', form=form, employee=employee)


@main.route('/employee/<int:employee_id>/delete', methods=['POST'])
@login_required
def delete_employee(employee_id):
    try:
        employee = employee_service.get_employee_by_id(employee_id)
        if not employee:
            flash('Сотрудник не найден', 'error')
            return redirect(url_for('main.employees'))
        
        employee_name = employee.full_name
        success = employee_service.delete_employee(employee_id)
        
        if success:
            auth_service.log_auth_event(
                current_user.username,
                'DELETE_EMPLOYEE',
                session_duration=f"Deleted employee: {employee_name}"
            )
            flash(f'Сотрудник "{employee_name}" успешно удален', 'success')
        else:
            flash('Ошибка при удалении сотрудника', 'error')
    except Exception as e:
        flash(f'Ошибка при удалении сотрудника: {str(e)}', 'error')
    
    return redirect(url_for('main.employees'))

@main.route('/user/logs')
@login_required
def user_logs():
    logs = auth_service.get_user_logs(current_user.id)
    return render_template('user_logs.html', logs=logs)

@main.route('/api/employees/search')
@login_required
def api_search_employees():
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
    
    try:
        employees = Employee.query.filter(
            Employee.full_name.ilike(f'%{query}%')
        ).limit(10).all()
        return jsonify([{
            'id': emp.id,
            'full_name': emp.full_name,
            'position': emp.position
        } for emp in employees])
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    # Новый маршрут для получения должностей через API
@main.route('/api/positions')
@login_required
def get_positions():
    """API endpoint для получения списка должностей"""
    try:
        positions = Employee.get_unique_positions()
        return jsonify(positions)
    except Exception as e:
        return jsonify({'error': str(e)}), 500