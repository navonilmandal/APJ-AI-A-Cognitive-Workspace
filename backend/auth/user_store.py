from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator
import re
from backend.auth.security import get_password_hash
from backend.database import Base, engine, SessionLocal
from backend.utils.logger import setup_logger

logger = setup_logger(__name__)

# Database Model
class UserDB(Base):
    __tablename__ = "users"
    
    username = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

# Pydantic Schemas
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=30, pattern="^[a-zA-Z0-9_]+$")
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72)

    @field_validator('password')
    @classmethod
    def password_complexity(cls, v: str) -> str:
        """
        Hardened password validation:
        - At least 1 uppercase letter
        - At least 1 lowercase letter
        - At least 1 digit
        - At least 1 special character
        """
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v

class UserInDB(BaseModel):
    username: str
    email: str
    hashed_password: str
    created_at: datetime

# Create tables
def init_db():
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully.")
        return True
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False

class UserStore:
    def get_user(self, username: str) -> Optional[UserInDB]:
        db = SessionLocal()
        try:
            user = db.query(UserDB).filter(UserDB.username == username).first()
            if user:
                return UserInDB(
                    username=user.username,
                    email=user.email,
                    hashed_password=user.hashed_password,
                    created_at=user.created_at
                )
            return None
        finally:
            db.close()

    def create_user(self, user: UserCreate) -> bool:
        db = SessionLocal()
        try:
            # Check if exists
            existing_user = db.query(UserDB).filter(UserDB.username == user.username).first()
            if existing_user:
                logger.warning(f"Signup failed: Username {user.username} already exists.")
                return False
            
            new_user = UserDB(
                username=user.username,
                email=str(user.email),
                hashed_password=get_password_hash(user.password)
            )
            db.add(new_user)
            db.commit()
            logger.info(f"User created successfully: {user.username}")
            return True
        except Exception as e:
            logger.error(f"Error creating user {user.username}: {e}")
            db.rollback()
            return False
        finally:
            db.close()

# Singleton
user_store = UserStore()
def get_user_store():
    return user_store
