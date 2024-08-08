from sqlalchemy import MetaData, Column, Table, String, Integer, Text, Boolean, ForeignKey, UniqueConstraint

metadata = MetaData()

user = Table(
    'user', 
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('username', String(20), unique=True, nullable=False),
    Column('name', String(20)),
    Column('email', String(length=320), unique=True, index=True, nullable=False),
    Column('hashed_password', String(length=1024), nullable=False),
    Column('is_active', Boolean, default=True, nullable=False),
    Column('is_superuser', Boolean, default=False, nullable=False),
    Column('is_verified', Boolean, default=False, nullable=False)
)

task = Table(
    'task', 
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('creator_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('title', String(20), nullable=False),
    Column('description', Text, nullable=False),
    Column('status', String(15), nullable=False),
    Column('priority', String(40), nullable=False)
)

privilege = Table(
    'privilege', 
    metadata,
    Column('t_id', Integer, ForeignKey('task.id'), nullable=False, primary_key=True),
    Column('u_id', Integer, ForeignKey('user.id'), nullable=False, primary_key=True),
    Column('read', Boolean, nullable=False),
    Column('edit', Boolean, nullable=False),
    UniqueConstraint('t_id', 'u_id', name='uix_task_user')
)
