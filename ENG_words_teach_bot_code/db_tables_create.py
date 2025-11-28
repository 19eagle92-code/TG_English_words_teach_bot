import sqlalchemy as sq
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "user"

    user_id = sq.Column(sq.Integer, primary_key=True)
    name
