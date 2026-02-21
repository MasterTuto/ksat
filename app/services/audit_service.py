from sqlalchemy.orm import Session
from app.models.database import AuditLog, User
from typing import Dict, Any, Optional, Union
from uuid import UUID
from datetime import datetime
import json


class AuditService:
    @staticmethod
    def log_create(
        db: Session,
        entity_type: str,
        entity_id: Union[str, UUID],
        new_values: Dict[str, Any],
        user_id: Optional[Union[str, UUID]] = None,
    ):
        """
        Cria um log de auditoria para operações de criação
        """
        audit_log = AuditLog(
            user_id=str(user_id) if user_id else None,
            entity_type=entity_type,
            entity_id=str(entity_id),
            action="create",
            old_values=None,
            new_values=json.dumps(new_values, default=str),
            created_at=datetime.utcnow(),
        )
        db.add(audit_log)
        db.commit()

    @staticmethod
    def log_update(
        db: Session,
        entity_type: str,
        entity_id: Union[str, UUID],
        old_values: Dict[str, Any],
        new_values: Dict[str, Any],
        user_id: Optional[Union[str, UUID]] = None,
    ):
        """
        Cria um log de auditoria para operações de atualização
        """
        audit_log = AuditLog(
            user_id=str(user_id) if user_id else None,
            entity_type=entity_type,
            entity_id=str(entity_id),
            action="update",
            old_values=json.dumps(old_values, default=str),
            new_values=json.dumps(new_values, default=str),
            created_at=datetime.utcnow(),
        )
        db.add(audit_log)
        db.commit()

    @staticmethod
    def log_delete(
        db: Session,
        entity_type: str,
        entity_id: Union[str, UUID],
        deleted_values: Dict[str, Any],
        user_id: Optional[Union[str, UUID]] = None,
    ):
        """
        Cria um log de auditoria para operações de exclusão
        """
        audit_log = AuditLog(
            user_id=str(user_id) if user_id else None,
            entity_type=entity_type,
            entity_id=str(entity_id),
            action="delete",
            old_values=json.dumps(deleted_values, default=str),
            new_values=None,
            created_at=datetime.utcnow(),
        )
        db.add(audit_log)
        db.commit()

    @staticmethod
    def log_vote(
        db: Session,
        entity_id: Union[str, UUID],
        vote_data: Dict[str, Any],
        user_id: Optional[Union[str, UUID]] = None,
    ):
        """
        Cria um log de auditoria para operações de voto
        """
        audit_log = AuditLog(
            user_id=str(user_id) if user_id else None,
            entity_type="vote",
            entity_id=str(entity_id),
            action="vote",
            old_values=None,
            new_values=json.dumps(vote_data, default=str),
            created_at=datetime.utcnow(),
        )
        db.add(audit_log)
        db.commit()

    @staticmethod
    def get_entity_history(db: Session, entity_type: str, entity_id: Union[str, UUID]):
        """
        Retorna o histórico completo de uma entidade
        """
        return (
            db.query(AuditLog)
            .filter(
                AuditLog.entity_type == entity_type,
                AuditLog.entity_id == str(entity_id),
            )
            .order_by(AuditLog.created_at.desc())
            .all()
        )

    @staticmethod
    def get_user_activity(db: Session, user_id: Union[str, UUID], limit: int = 100):
        """
        Retorna a atividade de um usuário específico
        """
        return (
            db.query(AuditLog)
            .filter(AuditLog.user_id == str(user_id))
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_recent_activity(
        db: Session, entity_type: Optional[str] = None, limit: int = 100
    ):
        """
        Retorna a atividade recente do sistema
        """
        query = db.query(AuditLog)

        if entity_type:
            query = query.filter(AuditLog.entity_type == entity_type)

        return query.order_by(AuditLog.created_at.desc()).limit(limit).all()
