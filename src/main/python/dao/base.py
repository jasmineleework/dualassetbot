"""
Base DAO with common CRUD operations
"""
from typing import TypeVar, Generic, Type, Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from core.database import Base
from loguru import logger

ModelType = TypeVar("ModelType", bound=Base)

class BaseDAO(Generic[ModelType]):
    """Base Data Access Object with common CRUD operations"""
    
    def __init__(self, model: Type[ModelType]):
        self.model = model
    
    def create(self, db: Session, **kwargs) -> ModelType:
        """Create a new record"""
        try:
            db_obj = self.model(**kwargs)
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create {self.model.__name__}: {e}")
            raise
    
    def get(self, db: Session, id: str) -> Optional[ModelType]:
        """Get a record by ID"""
        return db.query(self.model).filter(self.model.id == id).first()
    
    def get_multi(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        order_desc: bool = True
    ) -> List[ModelType]:
        """Get multiple records with optional filtering and pagination"""
        query = db.query(self.model)
        
        # Apply filters
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.filter(getattr(self.model, key) == value)
        
        # Apply ordering
        if order_by and hasattr(self.model, order_by):
            if order_desc:
                query = query.order_by(desc(getattr(self.model, order_by)))
            else:
                query = query.order_by(asc(getattr(self.model, order_by)))
        
        return query.offset(skip).limit(limit).all()
    
    def update(self, db: Session, id: str, **kwargs) -> Optional[ModelType]:
        """Update a record"""
        try:
            db_obj = self.get(db, id)
            if db_obj:
                for key, value in kwargs.items():
                    if hasattr(db_obj, key):
                        setattr(db_obj, key, value)
                db.commit()
                db.refresh(db_obj)
            return db_obj
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update {self.model.__name__}: {e}")
            raise
    
    def delete(self, db: Session, id: str) -> bool:
        """Delete a record"""
        try:
            db_obj = self.get(db, id)
            if db_obj:
                db.delete(db_obj)
                db.commit()
                return True
            return False
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to delete {self.model.__name__}: {e}")
            raise
    
    def count(self, db: Session, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records with optional filtering"""
        query = db.query(self.model)
        
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.filter(getattr(self.model, key) == value)
        
        return query.count()
    
    def exists(self, db: Session, **kwargs) -> bool:
        """Check if a record exists with given criteria"""
        query = db.query(self.model)
        
        for key, value in kwargs.items():
            if hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == value)
        
        return query.first() is not None