from sqlalchemy import String, Column, Integer, BigInteger, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

base = declarative_base()


class User(base):
    __table_args__ = {'quote': False}
    __tablename__ = "user"
    id = Column("Код", BigInteger, primary_key=True, quote=False)
    # имя
    first_name = Column("first_name", String, quote=False)
    # фамилия
    last_name = Column("last_name", String, quote=False)
    joined_at = Column("joined_at", DateTime, nullable=False, quote=False)
    last_message_at = Column("last_message_at", DateTime, nullable=False, quote=False)
    show_teacher_fullname = Column("show_teacher_fullname", Boolean, default=True, quote=False)
    default_group = Column("default_group", String(12), quote=False)
    show_room_info = Column("show_room_info", Boolean, default=False, quote=False)
    role_id = Column(Integer, ForeignKey('roles.id'), nullable=False, quote=False)
    show_group_info = Column("show_group_info", Boolean, default=False, quote=False)
    role = relationship("Role")


class Role(base):
    __tablename__ = 'role'
    id = Column(Integer, primary_key=True)
    name = Column(String)



