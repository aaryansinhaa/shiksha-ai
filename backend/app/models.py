import uuid
import datetime
from typing import List, Optional
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
from app.database import Base

class Language(Base):
    __tablename__ = "languages"
    id: Mapped[str] = mapped_column(sa.String(64), primary_key=True)
    lang_code: Mapped[str] = mapped_column(sa.String(8), index=True, unique=True)
    
    contexts: Mapped[List["Context"]] = relationship(back_populates="language")
    translations: Mapped[List["StrategyTranslation"]] = relationship(back_populates="language")

class Context(Base):
    __tablename__ = "contexts"
    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    context: Mapped[str] = mapped_column(sa.String())
    language_id: Mapped[str] = mapped_column(sa.ForeignKey("languages.id"))
    
    language: Mapped["Language"] = relationship(back_populates="contexts")

class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(sa.String(64), primary_key=True)
    client: Mapped[str] = mapped_column(sa.String(64), primary_key=True)
    language_id: Mapped[str] = mapped_column(sa.ForeignKey("languages.id"))
    study_subject: Mapped[Optional[str]] = mapped_column(sa.String())
    context_id: Mapped[str] = mapped_column(sa.String(256), default="0")
    context_title: Mapped[Optional[str]] = mapped_column(sa.String(256))

    conversation_state: Mapped[Optional["ConversationState"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", uselist=False, lazy="selectin"
    )
    interview_answers: Mapped[List["InterviewAnswer"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    strategies: Mapped[List["UserStrategy"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    llm_responses: Mapped[List["LlmResponse"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    evaluations: Mapped[List["StrategyEvaluation"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

class Strategy(Base):
    __tablename__ = "strategy"
    id: Mapped[str] = mapped_column(sa.String(), primary_key=True)

class StrategyTranslation(Base):
    __tablename__ = "strategy_translation"
    id: Mapped[str] = mapped_column(sa.String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    strategy: Mapped[str] = mapped_column(sa.ForeignKey("strategy.id"))
    name: Mapped[str] = mapped_column(sa.String())
    description: Mapped[str] = mapped_column(sa.String())
    language_id: Mapped[str] = mapped_column(sa.ForeignKey("languages.id"))

    language: Mapped["Language"] = relationship(back_populates="translations")

class StrategyEmbedding(Base):
    """RAG-based strategy embeddings (768-dim for Gemini text-embedding-004)."""
    __tablename__ = "strategy_embedding"
    strategy_id: Mapped[str] = mapped_column(sa.String(), primary_key=True)
    name: Mapped[str] = mapped_column(sa.String())
    phase: Mapped[Optional[str]] = mapped_column(sa.String())
    category: Mapped[Optional[str]] = mapped_column(sa.String())
    content: Mapped[Optional[str]] = mapped_column(sa.String())
    embedding = mapped_column(Vector(768), nullable=True)

class ConversationCompletedContexts(Base):
    __tablename__ = "conversation_completed_contexts"
    conversation_id: Mapped[str] = mapped_column(sa.ForeignKey("state.id", ondelete="CASCADE"), primary_key=True)
    completed_context_id: Mapped[int] = mapped_column(sa.ForeignKey("contexts.id", ondelete="CASCADE"), primary_key=True)

class ConversationState(Base):
    __tablename__ = "state"
    id: Mapped[str] = mapped_column(sa.String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(sa.String(64))
    user_client: Mapped[str] = mapped_column(sa.String(64))
    interview_completed: Mapped[bool] = mapped_column(sa.Boolean, default=False)
    current_turn: Mapped[int] = mapped_column(sa.Integer, default=0)
    current_context: Mapped[Optional[int]] = mapped_column(sa.ForeignKey("contexts.id"), nullable=True)
    strategy_for_frequency: Mapped[Optional[str]] = mapped_column(sa.ForeignKey("strategy.id"), nullable=True)
    current_conversation_step: Mapped[Optional[str]] = mapped_column(sa.String(32), default="intro")
    probe_count: Mapped[int] = mapped_column(sa.Integer, default=0)

    user: Mapped["User"] = relationship(back_populates="conversation_state")
    completed_contexts: Mapped[List["ConversationCompletedContexts"]] = relationship(cascade="all, delete-orphan", lazy="selectin")

    __table_args__ = (
        sa.ForeignKeyConstraint([user_id, user_client], [User.id, User.client], ondelete="CASCADE"),
    )

class InterviewAnswer(Base):
    __tablename__ = "interview_answer"
    id: Mapped[str] = mapped_column(sa.String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(sa.String(64))
    user_client: Mapped[str] = mapped_column(sa.String(64))
    context: Mapped[Optional[int]] = mapped_column(sa.ForeignKey("contexts.id"), nullable=True)
    strategy: Mapped[Optional[str]] = mapped_column(sa.ForeignKey("strategy.id"), nullable=True)
    turn: Mapped[int] = mapped_column(sa.Integer)
    message: Mapped[str] = mapped_column(sa.String())
    conversation_step: Mapped[str] = mapped_column(sa.String(32))
    message_time: Mapped[datetime.datetime] = mapped_column(server_default=sa.func.now())

    user: Mapped["User"] = relationship(back_populates="interview_answers")
    strategies: Mapped[List["UserStrategy"]] = relationship(back_populates="interview_answer")

    __table_args__ = (
        sa.ForeignKeyConstraint([user_id, user_client], [User.id, User.client], ondelete="CASCADE"),
    )

class UserStrategy(Base):
    __tablename__ = "user_strategy"
    id: Mapped[str] = mapped_column(sa.String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(sa.String(64))
    user_client: Mapped[str] = mapped_column(sa.String(64))
    interview_answer_id: Mapped[Optional[str]] = mapped_column(sa.ForeignKey("interview_answer.id"), nullable=True)
    context: Mapped[int] = mapped_column(sa.ForeignKey("contexts.id"))
    strategy: Mapped[str] = mapped_column(sa.ForeignKey("strategy.id"))
    frequency: Mapped[Optional[int]] = mapped_column(sa.Integer, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(server_default=sa.func.now())

    user: Mapped["User"] = relationship(back_populates="strategies")
    interview_answer: Mapped[Optional["InterviewAnswer"]] = relationship(back_populates="strategies")

    __table_args__ = (
        sa.ForeignKeyConstraint([user_id, user_client], [User.id, User.client], ondelete="CASCADE"),
    )

class LlmResponse(Base):
    __tablename__ = "llm_response"
    id: Mapped[str] = mapped_column(sa.String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(sa.String(64))
    user_client: Mapped[str] = mapped_column(sa.String(64))
    message: Mapped[str] = mapped_column(sa.String())
    context: Mapped[Optional[int]] = mapped_column(sa.ForeignKey("contexts.id"), nullable=True)
    strategy: Mapped[Optional[str]] = mapped_column(sa.ForeignKey("strategy.id"), nullable=True)
    turn: Mapped[int] = mapped_column(sa.Integer)
    conversation_step: Mapped[str] = mapped_column(sa.String(32))
    message_time: Mapped[datetime.datetime] = mapped_column(server_default=sa.func.now())

    user: Mapped["User"] = relationship(back_populates="llm_responses")

    __table_args__ = (
        sa.ForeignKeyConstraint([user_id, user_client], [User.id, User.client], ondelete="CASCADE"),
    )

class StrategyEvaluation(Base):
    __tablename__ = "strategy_evaluation"
    id: Mapped[str] = mapped_column(sa.String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(sa.String(64))
    user_client: Mapped[str] = mapped_column(sa.String(64))
    strategy: Mapped[str] = mapped_column(sa.ForeignKey("strategy.id"))
    SU: Mapped[bool] = mapped_column(sa.Boolean, default=False)
    SF: Mapped[float] = mapped_column(sa.Float())
    SC: Mapped[float] = mapped_column(sa.Float())

    user: Mapped["User"] = relationship(back_populates="evaluations")

    __table_args__ = (
        sa.ForeignKeyConstraint([user_id, user_client], [User.id, User.client], ondelete="CASCADE"),
    )

class ActivityLog(Base):
    __tablename__ = "activity_log"
    id: Mapped[str] = mapped_column(sa.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp: Mapped[int] = mapped_column(sa.BigInteger, index=True)
    user_id: Mapped[Optional[str]] = mapped_column(sa.String, index=True)
    user_client: Mapped[Optional[str]] = mapped_column(sa.String)
    action: Mapped[str] = mapped_column(sa.String, index=True)
    value: Mapped[Optional[dict]] = mapped_column(sa.JSON, nullable=True)
    context: Mapped[Optional[str]] = mapped_column(sa.String, nullable=True)
    strategy: Mapped[Optional[str]] = mapped_column(sa.String, nullable=True)
    turn: Mapped[Optional[int]] = mapped_column(sa.Integer, nullable=True)
    step: Mapped[Optional[str]] = mapped_column(sa.String, nullable=True)

class MouseTrace(Base):
    __tablename__ = "mouse_traces"
    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[str]] = mapped_column(sa.String(64))
    user_client: Mapped[Optional[str]] = mapped_column(sa.String(64))
    session_id: Mapped[Optional[str]] = mapped_column(sa.String(128))
    x: Mapped[int] = mapped_column(sa.Integer)
    y: Mapped[int] = mapped_column(sa.Integer)
    page_width: Mapped[Optional[int]] = mapped_column(sa.Integer, nullable=True)
    page_height: Mapped[Optional[int]] = mapped_column(sa.Integer, nullable=True)
    timestamp: Mapped[Optional[int]] = mapped_column(sa.BigInteger, nullable=True)

class SurveyResponse(Base):
    __tablename__ = "survey_responses"
    id: Mapped[str] = mapped_column(sa.String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    survey_id: Mapped[str] = mapped_column(sa.String(64), index=True)
    user_id: Mapped[str] = mapped_column(sa.String(64), index=True)
    user_client: Mapped[str] = mapped_column(sa.String(64))
    language: Mapped[str] = mapped_column(sa.String(8))
    responses: Mapped[dict] = mapped_column(sa.JSON)
    submitted_at: Mapped[datetime.datetime] = mapped_column(server_default=sa.func.now())

class Archive(Base):
    __tablename__ = "archive"
    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(sa.String(64), index=True)
    user_client: Mapped[str] = mapped_column(sa.String(64))
    archived_conversation: Mapped[str] = mapped_column(sa.String())
    archived_at: Mapped[datetime.datetime] = mapped_column(server_default=sa.func.now())

class Protocol(Base):
    __tablename__ = "protocols"
    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(sa.String(64), unique=True, index=True)
    title: Mapped[str] = mapped_column(sa.String(256))
    languages: Mapped[dict] = mapped_column(sa.JSON)
    steps: Mapped[dict] = mapped_column(sa.JSON)
    created_at: Mapped[datetime.datetime] = mapped_column(server_default=sa.func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(server_default=sa.func.now(), onupdate=sa.func.now())
