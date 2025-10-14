from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from app.models import Employee
from app import db

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/employees')
def employees():
    try:
        page = request.args.get('page', 1, type=int)
        search_query = request.args.get('search', '')
        
        # Простой запрос для тестирования
        if search_query:
            employees_query = Employee.query.filter(Employee.full_name.ilike(f'%{search_query}%'))
        else:
            employees_query = Employee.query
        
        employees = employees_query.paginate(page=page, per_page=20, error_out=False)
        
        return render_template(
            'employees.html',
            employees=employees.items,
            pagination=employees,
            search_query=search_query
        )
    except Exception as e:
        print(f"Error: {e}")  # Для отладки
        flash(f'Error loading employees: {str(e)}', 'error')
        return render_template('employees.html', employees=[])

@main.route('/test-db')
def test_db():
    try:
        employees = Employee.query.limit(5).all()
        return jsonify([{
            'id': emp.id,
            'name': emp.full_name,
            'position': emp.position
        } for emp in employees])
    except Exception as e:
        return jsonify({'error': str(e)}), 500