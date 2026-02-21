#!/usr/bin/env python3
"""
Script para implementar sistema de login com API endpoints
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal, create_tables
from app.models.database import User
from app.models.user_password_mixin import UserPasswordMixin
from app.models.user_extension import UserExtension
from app.services.calculation_service import CalculationService
from uuid import uuid4
from datetime import datetime, timedelta
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, status, Header, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import jwt
from datetime import datetime, timedelta

from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext

# Configurações JWT
SECRET_KEY = "dindin-secret-key"  # Em produção usar variáveis de ambiente
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 7  # 7 dias

# Contexto para hash de senha
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Instanciar o OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI(title="Dindin API", version="1.0.0")


# Dependências
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_access_token(data: dict) -> str:
    """Cria token de acesso"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded


def get_current_user(token: str = Depends(oauth2_scheme)) -> Optional[dict]:
    """Obtém usuário atual do token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            return None
        return {"username": username}
    except:
        return None


# Modelos Pydantic
class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    token: str
    expires_at: datetime


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    currency_balance: float
    created_at: datetime
    updated_at: datetime


class UserRegister(BaseModel):
    username: str
    email: str
    password: str


class UserLoginResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    token: str
    expires_at: datetime
    user: UserResponse


# Endpoints de autenticação
@app.post("/token", response_model=Token, status_code=status.HTTP_200_OK)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == form_data.username).first()

    if not user or not hasattr(user, "password_hash"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha inválidos",
        )

    if not pwd_context.verify(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha inválidos",
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": int(access_token_expires.total_seconds()),
        "expires_at": (datetime.utcnow() + access_token_expires).isoformat(),
        "token": access_token,
    }


@app.post("/register", response_model=UserRegister, status_code=status.HTTP_201_CREATED)
def register(form_data: UserRegister, db: Session = Depends(get_db)):
    # Verificar se usuário já existe
    existing_user = (
        db.query(User)
        .filter((User.username == form_data.username) | (User.email == form_data.email))
        .first()
    )

    if existing_user:
        raise HTTPException(status_code=400, detail="Usuário ou email já existente")

    # Criar novo usuário com senha hash
    hashed_password = pwd_context.hash(form_data.password)

    user = User(
        username=form_data.username,
        email=form_data.email,
        currency_balance=1000.0,  # 1_000 unidades iniciais
    )
    user.password_hash = hashed_password

    db.add(user)
    db.commit()
    db.refresh(user)

    return UserResponse(
        id=str(user.id),
        username=user.username,
        email=user.email,
        currency_balance=float(user.currency_balance),
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@app.get("/me", response_model=UserResponse)
def get_current_user_info(
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    if current_user is None:
        raise HTTPException(status_code=401, detail="Token inválido")

    # Buscar dados completos do usuário
    user = db.query(User).filter(User.username == current_user["username"]).first()

    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    return UserResponse(
        id=str(user.id),
        username=user.username,
        email=user.email,
        currency_balance=float(user.currency_balance),
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


# Endpoint de verificação de token
@app.post("/token/verify", response_model=dict)
async def verify_token(token: str = Header(...), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return {"valid": True, "payload": payload}
    except Exception:
        return {"valid": False, "error": "Token inválido"}


# Endpoint para logout
@app.post("/logout")
async def logout():
    # Implementar invalidação de token (lado cliente) seria ideal)
    return {"message": "Logout realizado com sucesso"}


# Endpoint para alterar senha
@app.put("/me/password")
async def change_password(
    current_user: dict = Depends(get_current_user),
    current_password: str = Form(...),
    new_password: str = Form(...),
    db: Session = Depends(get_db),
):
    if current_user is None:
        raise HTTPException(status_code=401, detail="Usuário não autenticado")

    user = db.query(User).filter(User.username == current_user["username"]).first()

    if not user or not hasattr(user, "password_hash"):
        raise HTTPException(status_code=400, detail="Senha atual não definida")

    # Verificar senha atual
    if not pwd_context.verify(current_password, user.password_hash):
        raise HTTPException(status_code=401, detail="Senha atual incorreta")

    # Verificar nova senha
    if not new_password or len(new_password) < 6:
        raise HTTPException(
            status_code=400, detail="Nova senha deve ter pelo menos 6 caracteres"
        )

    # Atualizar senha
    user.password_hash = pwd_context.hash(new_password)
    user.updated_at = datetime.utcnow()

    db.commit()

    return {"message": "Senha alterada com sucesso"}


# Endpoint para informações do usuário
@app.get("/me/info", response_model=dict)
async def get_user_info(
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    if current_user is None:
        raise HTTPException(status_code=401, detail="Usuário não autenticado")

    user = db.query(User).filter(User.username == current_user["username"]).first()

    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    return {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "currency_balance": float(user.currency_balance),
        "created_at": user.created_at.isoformat(),
        "updated_at": user.updated_at.isoformat(),
    }


if __name__ == "__main__":
    print("=== SISTEMA DE LOGIN - DINDIN ===")
    print("1. Iniciando servidor de login...")
    print("2. Endpoint: POST /token - Obter token de acesso")
    print("3. Endpoint: POST /register - Criar nova conta")
    print("4. Endpoint: POST /token/verify - Verificar token")
    print("5. Endpoint: GET /me - Informações do usuário logado")
    print("6. Endpoint: PUT /me/password - Alterar senha")
    print("7. Endpoint: POST /logout - Logout")
    print("8. Endpoint: GET /me/info - Informações detalhadas do usuário")
    print(
        "\nUse 'python create_login_system.py' para configuração inicial se necessário."
    )
    print("Acesse http://localhost:8000/docs para ver documentação completa da API.")
    print("\nSistema pronto para uso com autenticação JWT!")

    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
