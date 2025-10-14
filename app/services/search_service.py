from abc import ABC, abstractmethod
from app.models import Employee
from typing import List, Tuple, Optional
from sqlalchemy import or_, and_

class ISearchService(ABC):
    @abstractmethod
    def search_employees(self, query: str, page: int, per_page: int, min_salary: Optional[int] = None, max_salary: Optional[int] = None) -> List[Employee]:
        pass
    
    @abstractmethod
    def get_sorted_employees(self, sort_by: str, sort_order: str, page: int, per_page: int, min_salary: Optional[int] = None, max_salary: Optional[int] = None) -> List[Employee]:
        pass

class SearchService(ISearchService):
    def search_employees(self, query: str, page: int = 1, per_page: int = 20, min_salary: Optional[int] = None, max_salary: Optional[int] = None):
        search_filter = or_(
            Employee.full_name.ilike(f'%{query}%'),
            Employee.position.ilike(f'%{query}%')
        )
        
        # Добавляем фильтр по зарплате
        salary_filters = []
        if min_salary is not None:
            salary_filters.append(Employee.salary >= min_salary)
        if max_salary is not None:
            salary_filters.append(Employee.salary <= max_salary)
        
        # Объединяем фильтры
        if salary_filters:
            final_filter = and_(search_filter, *salary_filters)
        else:
            final_filter = search_filter
            
        return Employee.query.filter(final_filter).paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
    
    def get_sorted_employees(self, sort_by: str, sort_order: str, page: int = 1, per_page: int = 20, min_salary: Optional[int] = None, max_salary: Optional[int] = None):
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
        
        return query.order_by(sort_column).paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )