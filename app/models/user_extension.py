from sqlalchemy import (
    Column,
    String,
    Text,
    Boolean,
    DateTime,
    DECIMAL,
    Integer,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime


# Extensão do modelo User para suporte a moeda global
class UserExtension:
    """Mixin para adicionar suporte a moeda ao modelo User"""

    # Adicionar estes atributos ao modelo User existente
    currency_balance = Column(DECIMAL(15, 8), default=1000.0)  # X inicial = 1_000

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "currency_balance" not in kwargs:
            self.currency_balance = 1000.0
