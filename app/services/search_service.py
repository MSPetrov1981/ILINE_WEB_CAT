from abc import ABC, abstractmethod
from app.models import Employee
from typing import List, Tuple
from sqlalchemy import or_

class ISearchService(ABC):
    @abstractmethod
    def search_employees(self, query: str, page: int, per_page: int) -> List[Employee]:
        pass
    
    @abstractmethod
    def get_sorted_employees(self, sort_by: str, sort_order: str, page: int, per_page: int) -> List[Employee]:
        pass

class SearchService(ISearchService):
    def search_employees(self, query: str, page: int = 1, per_page: int = 20) -> List[Employee]:
        search_filter = or_(
            Employee.full_name.ilike(f'%{query}%'),
            Employee.position.ilike(f'%{query}%')
        )
        return Employee.query.filter(search_filter).paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
    
    def get_sorted_employees(self, sort_by: str, sort_order: str, page: int = 1, per_page: int = 20) -> List[Employee]:
        sort_column = getattr(Employee, sort_by, Employee.id)
        if sort_order == 'desc':
            sort_column = sort_column.desc()
        return Employee.query.order_by(sort_column).paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )