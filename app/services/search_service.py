from abc import ABC, abstractmethod
from app.models import Employee
from typing import List, Tuple, Optional
from sqlalchemy import or_, and_
from datetime import datetime, date

class ISearchService(ABC):
    @abstractmethod
    def search_employees(self, query: str, page: int, per_page: int, 
                        min_salary: Optional[int] = None, 
                        max_salary: Optional[int] = None,
                        start_date: Optional[date] = None,
                        end_date: Optional[date] = None) -> List[Employee]:
        pass
    
    @abstractmethod
    def get_sorted_employees(self, sort_by: str, sort_order: str, page: int, per_page: int, 
                           min_salary: Optional[int] = None, 
                           max_salary: Optional[int] = None,
                           start_date: Optional[date] = None,
                           end_date: Optional[date] = None) -> List[Employee]:
        pass

class SearchService(ISearchService):
    def search_employees(self, query: str, page: int = 1, per_page: int = 20, 
                        min_salary: Optional[int] = None, 
                        max_salary: Optional[int] = None,
                        start_date: Optional[date] = None,
                        end_date: Optional[date] = None):
        
        # Создаем базовый запрос
        query_obj = Employee.query
        
        # Добавляем поисковый фильтр только если есть query
        if query:
            search_filter = or_(
                Employee.full_name.ilike(f'%{query}%'),
                Employee.position.ilike(f'%{query}%')
            )
            query_obj = query_obj.filter(search_filter)
        
        # Добавляем фильтр по зарплате
        if min_salary is not None:
            query_obj = query_obj.filter(Employee.salary >= min_salary)
        if max_salary is not None:
            query_obj = query_obj.filter(Employee.salary <= max_salary)
        
        # Добавляем фильтр по дате приема
        if start_date is not None:
            query_obj = query_obj.filter(Employee.hire_date >= start_date)
        if end_date is not None:
            query_obj = query_obj.filter(Employee.hire_date <= end_date)
        
        return query_obj.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
    
    def get_sorted_employees(self, sort_by: str, sort_order: str, page: int = 1, per_page: int = 20, 
                           min_salary: Optional[int] = None, 
                           max_salary: Optional[int] = None,
                           start_date: Optional[date] = None,
                           end_date: Optional[date] = None):
        sort_column = getattr(Employee, sort_by, Employee.id)
        if sort_order == 'desc':
            sort_column = sort_column.desc()
        
        # Создаем базовый запрос
        query = Employee.query
        
        # Добавляем фильтр по зарплате
        if min_salary is not None:
            query = query.filter(Employee.salary >= min_salary)
        if max_salary is not None:
            query = query.filter(Employee.salary <= max_salary)
        
        # Добавляем фильтр по дате приема
        if start_date is not None:
            query = query.filter(Employee.hire_date >= start_date)
        if end_date is not None:
            query = query.filter(Employee.hire_date <= end_date)
        
        return query.order_by(sort_column).paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )