from abc import ABC, abstractmethod
from app.models import Employee
from app import db
from typing import List, Optional
from datetime import date

class IEmployeeService(ABC):
    @abstractmethod
    def get_all_employees(self, page: int, per_page: int) -> List[Employee]:
        pass
    
    @abstractmethod
    def get_employee_by_id(self, employee_id: int) -> Optional[Employee]:
        pass
    
    @abstractmethod
    def update_employee(self, employee_id: int, **kwargs) -> Optional[Employee]:
        pass
    
    @abstractmethod
    def create_employee(self, **kwargs) -> Employee:
        pass
    
    @abstractmethod
    def delete_employee(self, employee_id: int) -> bool:
        pass

class EmployeeService(IEmployeeService):
    def get_all_employees(self, page: int = 1, per_page: int = 20):
        return Employee.query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
    
    def get_employee_by_id(self, employee_id: int):
        return Employee.query.get(employee_id)
    
    def update_employee(self, employee_id: int, **kwargs):
        employee = self.get_employee_by_id(employee_id)
        if employee:
            for key, value in kwargs.items():
                if hasattr(employee, key) and value is not None:
                    setattr(employee, key, value)
            db.session.commit()
        return employee
    
    def create_employee(self, **kwargs):
        employee = Employee(**kwargs)
        db.session.add(employee)
        db.session.commit()
        return employee
    
    def delete_employee(self, employee_id: int):
        employee = self.get_employee_by_id(employee_id)
        if employee:
            # Перед удалением обнуляем ссылки на этого сотрудника как руководителя
            subordinates = Employee.query.filter_by(boss_id=employee_id).all()
            for subordinate in subordinates:
                subordinate.boss_id = None
            
            db.session.delete(employee)
            db.session.commit()
            return True
        return False