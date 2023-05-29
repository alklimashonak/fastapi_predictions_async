from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTableUUID

from src.database import Base


class User(SQLAlchemyBaseUserTableUUID, Base):
    __tablename__ = 'users'

