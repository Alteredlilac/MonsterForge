"""
Shared SQLAlchemy declarative base and primary-key helper for every ORM
model in db/.

Split out from db/session.py so model modules (reference_data.py,
scraping.py, pipeline.py, cards.py) can import Base without also pulling
in engine/session setup, and so db/session.py can import Base for
Base.metadata.create_all() without depending on any specific model
module.
"""

import uuid

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def uuid4_str() -> str:
    """Generate a UUID4 as a string, for use as a default on TEXT primary keys.

    Every table in db/ uses a UUID4 primary key stored as TEXT rather
    than an autoincrementing integer, so IDs can be generated
    application-side before a row is ever written — useful once multiple
    scraping/processing sources need to generate identifiers without
    coordinating on a shared counter. TEXT rather than BLOB: readability
    during manual debugging/inspection outweighs the storage saving,
    irrelevant at this project's scale.
    """
    return str(uuid.uuid4())
