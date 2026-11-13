"""Autenticación OAuth2 simple y administración de cuentas."""

from datetime import datetime, timedelta, timezone
import base64
import hashlib
import hmac
import json
import os
import secrets

from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")
TOKEN_TTL_HOURS = 12

def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

def _secret() -> bytes:
    value = os.getenv("AUTH_SECRET_KEY", "")
    if len(value) < 32:
        raise HTTPException(status_code=503, detail="Configure AUTH_SECRET_KEY (mínimo 32 caracteres).")
    return value.encode()

def _hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 310000)
    return f"{_b64(salt)}.{_b64(digest)}"

def _verify_password(password: str, stored: str) -> bool:
    try:
        salt_text, digest_text = stored.split(".", 1)
        salt = base64.urlsafe_b64decode(salt_text + "=" * (-len(salt_text) % 4))
        expected = base64.urlsafe_b64decode(digest_text + "=" * (-len(digest_text) % 4))
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 310000)
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False

def _token(user: User) -> str:
    now = int(datetime.now(timezone.utc).timestamp())
    head = _b64(b'{"alg":"HS256","typ":"JWT"}')
    body = _b64(json.dumps({"sub": str(user.id), "exp": now + TOKEN_TTL_HOURS * 3600}).encode())
    signature = _b64(hmac.new(_secret(), f"{head}.{body}".encode(), hashlib.sha256).digest())
    return f"{head}.{body}.{signature}"

class UserCreate(BaseModel):
    email: EmailStr
    nombre: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=8, max_length=128)

class UserUpdate(BaseModel):
    email: EmailStr | None = None
    nombre: str | None = Field(default=None, min_length=1, max_length=120)
    password: str | None = Field(default=None, min_length=8, max_length=128)

class UserRead(BaseModel):
    id: int
    email: str
    nombre: str
    activo: bool
    eliminado_en: datetime | None

    model_config = {"from_attributes": True}

def require_admin(x_admin_key: str | None = Header(default=None)):
    expected = os.getenv("ADMIN_API_KEY", "")
    if not expected or not x_admin_key or not hmac.compare_digest(x_admin_key, expected):
        raise HTTPException(status_code=401, detail="Clave administrativa inválida.")

def current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    try:
        head, body, signature = token.split(".")
        expected = _b64(hmac.new(_secret(), f"{head}.{body}".encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected):
            raise ValueError()
        payload = json.loads(base64.urlsafe_b64decode(body + "=" * (-len(body) % 4)))
        if payload["exp"] < int(datetime.now(timezone.utc).timestamp()):
            raise ValueError()
        user = db.get(User, int(payload["sub"]))
        if user is None or not user.activo:
            raise ValueError()
        return user
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Token inválido o vencido.", headers={"WWW-Authenticate": "Bearer"}) from exc

@router.post("/auth/token")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == form.username.lower()))
    if user is None or not user.activo or not _verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas.", headers={"WWW-Authenticate": "Bearer"})
    return {"access_token": _token(user), "token_type": "bearer", "expires_in": TOKEN_TTL_HOURS * 3600}

@router.get("/auth/me", response_model=UserRead)
def me(user: User = Depends(current_user)):
    return user

@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin)])
def create_user(data: UserCreate, db: Session = Depends(get_db)):
    email = str(data.email).lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="Ese correo ya está registrado.")
    user = User(email=email, nombre=data.nombre, password_hash=_hash_password(data.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.get("/users", response_model=list[UserRead], dependencies=[Depends(require_admin)])
def list_users(db: Session = Depends(get_db)):
    return list(db.scalars(select(User).order_by(User.id)).all())

@router.put("/users/{user_id}", response_model=UserRead, dependencies=[Depends(require_admin)])
def update_user(user_id: int, data: UserUpdate, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    values = data.model_dump(exclude_unset=True)
    if "email" in values:
        values["email"] = str(values["email"]).lower()
        duplicate = db.scalar(select(User).where(User.email == values["email"], User.id != user_id))
        if duplicate:
            raise HTTPException(status_code=409, detail="Ese correo ya está registrado.")
    if "password" in values:
        values["password_hash"] = _hash_password(values.pop("password"))
    for key, value in values.items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user

@router.delete("/users/{user_id}", response_model=UserRead, dependencies=[Depends(require_admin)])
def deactivate_user(user_id: int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    user.activo = False
    user.eliminado_en = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)
    return user
