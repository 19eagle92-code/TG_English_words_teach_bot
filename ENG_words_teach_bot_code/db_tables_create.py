import sqlalchemy as sq
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy import UniqueConstraint
from sqlalchemy.exc import IntegrityError

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    user_id = sq.Column(sq.Integer, primary_key=True)
    chat_id = sq.Column(sq.Integer, unique=True, nullable=False)
    user_name = sq.Column(sq.String(100), nullable=True)

    def __repr__(self):
        return (
            f"<User(id={self.user_id}, chat_id={self.chat_id}, name={self.user_name})>"
        )


class RussianWord(Base):
    __tablename__ = "russian_words"
    ru_word_id = sq.Column(sq.Integer, primary_key=True)
    ru_word = sq.Column(sq.String(200), nullable=False)
    user_id = sq.Column(sq.Integer, sq.ForeignKey("users.user_id"), nullable=False)

    user = relationship("User", back_populates="russian_words")
    english_words = relationship(
        "EnglishWord", back_populates="russian_word", cascade="all, delete-orphan"
    )

    __table_args__ = (UniqueConstraint("user_id", "ru_word", name="uq_user_ru_word"),)

    def __repr__(self):
        return f"<RussianWord(id={self.ru_word_id}, word={self.ru_word}, user_id={self.user_id})>"


class EnglishWord(Base):
    __tablename__ = "english_words"
    en_word_id = sq.Column(sq.Integer, primary_key=True)
    en_word = sq.Column(sq.String(200), nullable=False)
    ru_word_id = sq.Column(
        sq.Integer, sq.ForeignKey("russian_words.ru_word_id"), nullable=False
    )

    russian_word = relationship("RussianWord", back_populates="english_words")

    def __repr__(self):
        return f"<EnglishWord(id={self.en_word_id}, word={self.en_word}, ru_word_id={self.ru_word_id})>"


User.russian_words = relationship(
    "RussianWord", back_populates="user", cascade="all, delete-orphan"
)


def create_tables(engine):
    """Создать все таблицы"""
    Base.metadata.create_all(engine)
