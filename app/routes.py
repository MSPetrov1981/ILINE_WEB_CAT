from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from app.services.employee_service import EmployeeService
from app.services.search_service import SearchService
from app.models import Employee
from app import db

main = Blueprint('main', __name__)

employee_service = EmployeeService()
search_service = SearchService()

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/employees')
def employees():
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '')
    sort_by = request.args.get('sort_by', 'id')
    sort_order = request.args.get('sort_order', 'asc')
    
    try:
        if search_query:
            pagination = search_service.search_employees(search_query, page, 20)
        else:
            pagination = search_service.get_sorted_employees(sort_by, sort_order, page, 20)
        
        employees = pagination.items
        return render_template(
            'employees.html',
            employees=employees,
            pagination=pagination,
            search_query=search_query,
            sort_by=sort_by,
            sort_order=sort_order
        )
    except Exception as e:
        flash(f'Error loading employees: {str(e)}', 'error')
        return render_template('employees.html', employees=[])

@main.route('/employee/<int:employee_id>', methods=['GET', 'POST'])
def edit_employee(employee_id):
    employee = employee_service.get_employee_by_id(employee_id)
    if not employee:
        flash('Employee not found', 'error')
        return redirect(url_for('main.employees'))
    
    if request.method == 'POST':
        try:
            full_name = request.form.get('full_name')
            position = request.form.get('position')
            salary = request.form.get('salary', type=int)
            boss_id = request.form.get('boss_id', type=int)
            
            employee_service.update_employee(
                employee_id,
                full_name=full_name,
                position=position,
                salary=salary,
                boss_id=boss_id if boss_id else None
            )
            flash('Employee updated successfully', 'success')
        except Exception as e:
            flash(f'Error updating employee: {str(e)}', 'error')
    
    bosses = Employee.query.filter(Employee.id != employee_id).all()
    return render_template('edit_employee.html', employee=employee, bosses=bosses)

@main.route('/api/employees/search')
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