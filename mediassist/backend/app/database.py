import re
from time import perf_counter

from sqlalchemy import create_engine
from sqlalchemy import event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings
from app.services.metrics import DATABASE_STATEMENTS_TOTAL, DATABASE_STATEMENT_DURATION_SECONDS


connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    connect_args=connect_args,
)


def _sql_operation(statement: str) -> str:
    """Return a small, non-sensitive SQL operation label; never expose SQL."""
    match = re.match(r"\s*([a-zA-Z]+)", statement or "")
    operation = match.group(1).upper() if match else "OTHER"
    return operation if operation in {"SELECT", "INSERT", "UPDATE", "DELETE"} else "OTHER"


@event.listens_for(engine, "before_cursor_execute")
def _start_statement_timer(conn, cursor, statement, parameters, context, executemany):
    if context is not None:
        context._mediassist_statement_started = perf_counter()
        context._mediassist_statement_operation = _sql_operation(statement)


def _finish_statement(context, outcome: str) -> None:
    if context is None:
        return
    started = getattr(context, "_mediassist_statement_started", None)
    if started is None:
        return
    operation = getattr(context, "_mediassist_statement_operation", "OTHER")
    DATABASE_STATEMENTS_TOTAL.labels(operation=operation, outcome=outcome).inc()
    DATABASE_STATEMENT_DURATION_SECONDS.labels(operation=operation).observe(perf_counter() - started)
    context._mediassist_statement_started = None


@event.listens_for(engine, "after_cursor_execute")
def _record_statement_success(conn, cursor, statement, parameters, context, executemany):
    _finish_statement(context, "success")


@event.listens_for(engine, "handle_error")
def _record_statement_error(exception_context):
    _finish_statement(getattr(exception_context, "execution_context", None), "error")


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
