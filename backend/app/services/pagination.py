from sqlalchemy import func, select
from sqlalchemy.orm import Session


def paginate_query(db: Session, statement, page: int, size: int):
    total_statement = select(func.count()).select_from(
        statement.order_by(None).subquery()
    )
    total = db.scalar(total_statement) or 0

    items_statement = (
        statement
        .offset((page - 1) * size)
        .limit(size)
    )
    items = list(db.scalars(items_statement).all())

    return {
        "items": items,
        "page": page,
        "size": size,
        "total": total,
    }


def paginate_items(items: list, page: int, size: int):
    total = len(items)
    start = (page - 1) * size

    return {
        "items": items[start:start + size],
        "page": page,
        "size": size,
        "total": total,
    }
