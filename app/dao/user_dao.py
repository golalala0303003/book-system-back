from sqlmodel import Session, select
from app.models.user import User
from fastapi import Depends
from app.core.db import get_db

class UserDao:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db


    def get_user_by_username(self, username: str) -> User | None:
        statement = select(User).where(User.username == username)
        return self.db.exec(statement).first()


    def get_user_by_id(self, user_id: int) -> User | None:
        statement = select(User).where(User.id == user_id)
        return self.db.exec(statement).first()


    def create_user(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
