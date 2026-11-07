from sqlalchemy import Integer, String, Text, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base


class Lesson(Base):
    __tablename__ = "lessons"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    title: Mapped[str] = mapped_column(String(180))
    learning_objective: Mapped[str] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    created_at: Mapped[str] = mapped_column(String(40))
    updated_at: Mapped[str] = mapped_column(String(40))
    data: Mapped[dict] = mapped_column(JSON, default=dict)
    revision: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    __mapper_args__ = {"version_id_col": revision}


class LessonVersion(Base):
    __tablename__ = "lesson_versions"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    lesson_id: Mapped[str] = mapped_column(ForeignKey("lessons.id"), index=True)
    version: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[str] = mapped_column(String(40))
    sections: Mapped[list] = mapped_column(JSON)


class AuditHistory(Base):
    __tablename__ = "audit_history"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    lesson_id: Mapped[str] = mapped_column(ForeignKey("lessons.id"), index=True)
    report: Mapped[dict] = mapped_column(JSON)
