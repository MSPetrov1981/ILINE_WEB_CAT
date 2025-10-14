from abc import ABC, abstractmethod
from app.models import Employee
from app import db
from typing import List, Optional

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

class EmployeeService(IEmployeeService):
    def get_all_employees(self, page: int = 1, per_page: int = 20) -> List[Employee]:
        return Employee.query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
    
    def get_employee_by_id(self, employee_id: int) -> Optional[Employee]:
        return Employee.query.get(employee_id)
    
    def update_employee(self, employee_id: int, **kwargs) -> Optional[Employee]:
        employee = self.get_employee_by_id(employee_id)
        if employee:
            for key, value in kwargs.items():
                if hasattr(employee, key):
                    setattr(employee, key, value)
            db.session.commit()
        return employee