import sqlalchemy as sa
from sqlalchemy import orm

metadata = sa.MetaData()
Base = orm.declarative_base(metadata=metadata)
