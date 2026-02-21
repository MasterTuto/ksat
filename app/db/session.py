from app.core.database import SessionLocal
from app.models.database import Base


def get_db():
    """
    Função de dependência para obter sessão do banco de dados
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """
    Cria todas as tabelas no banco de dados
    """
    Base.metadata.create_all(bind=SessionLocal().bind)
