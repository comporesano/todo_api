from fastapi_users import fastapi_users, FastAPIUsers
from fastapi import FastAPI, Depends
from auth.manager import get_user_manager
from auth.schemas import UserCreate, UserRead   
from database.database import User, get_async_session
from models.models import task, privilege, user
from auth.auth import auth_backend
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select, update
from enum import Enum


class TaskStatus(Enum):
    CREATED = "created"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class TaskPriority(Enum):
    UI = "urgent_important"
    UNI = "urgent_not_important"
    NUI = "not_urgent_important"
    NUNI = "not_urgent_not_important"


app = FastAPI(
    title='Todo'
)

fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)

app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix='/auth/jwt',
    tags=['auth'],
)

app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)

cur_user = fastapi_users.current_user()


def validate_status(status: str) -> bool:
    access_list = [status.value for status in TaskStatus]
    if status in access_list:
        return True
    else:
        return False
    

def validate_priority(priority: str) -> bool:
    access_list = [priority.value for priority in TaskPriority]
    if priority in access_list:
        return True
    else:
        return False


async def get_task_data(task_id: int,
                        session: AsyncSession) -> dict:
    query = select(task).where(task.c.id == task_id)
    result = await session.execute(query)
    task_row = result.fetchone()
    keys = ['id', 'creator_id', 'title', 'description', 'status', 'priority']
    
    return dict(zip(keys, list(task_row)))
       

async def check_task_creator(task_id: int, 
                             session: AsyncSession) -> int:
    query = select(task.c.creator_id).where(task.c.id == task_id)
    result = await session.execute(query)
    creator_id = result.scalars().first()

    return creator_id


async def get_users(session: AsyncSession) -> list:
    query = select(user.c.id)
    result = await session.execute(query)
    ids = result.scalars().all()
    
    return list(ids)


async def get_tasks(session: AsyncSession) -> list:
    query = select(task.c.id)
    result = await session.execute(query)
    ids = result.scalars().all()
    
    return list(ids)



async def get_privileges(task_id: int,
                         user_id: int,
                         session: AsyncSession) -> dict:
    query = select(privilege.c.read, privilege.c.edit).where(and_(privilege.c.t_id == task_id, 
                                                                  privilege.c.u_id == user_id))
    result = await session.execute(query)
    privilege_row = result.fetchone()
    try:
        read, edit = privilege_row
    except Exception:
        return {'read': False,
                'edit': False}
    if privilege_row:
        return {'read': read,
                'edit': edit}
    else:
        return {'read': False,
                'edit': False}
    

@app.post("/create-task/")
async def create_task(user: User = Depends(cur_user),
                      session: AsyncSession = Depends(get_async_session),
                      title: str = 'Foo', 
                      description: str = 'Foo', 
                      priority: str = "not_urgent_not_important") -> dict:
    if not  validate_priority(priority=priority):
        priority = "not_urgent_not_important"
    new_task = task.insert().values(
        title=title,
        description=description,
        status='created',
        priority=priority,
        creator_id=user.id
    )

    result = await session.execute(new_task)
    await session.commit()

    task_id = result.inserted_primary_key[0]

    new_privilege = privilege.insert().values(
        t_id=task_id,
        u_id=user.id,
        read=True,
        edit=True
    )
    await session.execute(new_privilege)
    await session.commit()
    
    return {'data': f'Task(task_id: {task_id}) created by user: {user.id}'}


@app.post("/grant/")
async def grant_privilege(task_id: int,
                          target_user_id: int,
                          read: bool | None = False,
                          edit: bool | None = False ,
                          user: User = Depends(cur_user),
                          session: AsyncSession = Depends(get_async_session)) -> dict:
    try:
        if await check_task_creator(task_id=task_id, session=session) == user.id:
            new_privilege = privilege.insert().values(
                t_id=task_id,
                u_id=target_user_id,
                read=read,
                edit=edit
            )
            await session.execute(new_privilege)
            await session.commit()
            return {'data': f'Granted privileges (r: {read}, e: {edit}) granted by user: {user.id}'}
        else:
            return {'data': f'User {user.id} have no access to this task'}
    except IntegrityError:
        await session.rollback()
        return {'data': 'Integrity error. Privilege already exist.'}


@app.get('/task/{task_id}/get')
async def get_task(task_id: int,
                   user: User = Depends(cur_user),
                   session: AsyncSession = Depends(get_async_session)) -> dict:
    privileges = await get_privileges(task_id=task_id, user_id=user.id, session=session)
    if task_id in await get_tasks(session=session):
        if privileges.get('read'): 
            query = select(task)
            result = await session.execute(query)
            tasks = result.fetchall()[0]
            keys = ['task_id', 'creator_id', 'title', 'description', 'status', 'priority']
            return {'data': dict(zip(keys, list(tasks)))}
        else:
            return {'data': f'User {user.id} has no privileges for reading task {task_id}'}
    else:
        return {'data': f'No task with id - {task_id}'}


@app.post('/task/{task_id}/edit')
async def edit_task(task_id: int,
                    title: str | None = None,
                    description: str | None = None, 
                    priority: str | None = None,
                    status: str | None = None,
                    user: User = Depends(cur_user),
                    session: AsyncSession = Depends(get_async_session)) -> dict:
    privileges = await get_privileges(task_id=task_id, user_id=user.id, session=session)
    
    if task_id in await get_tasks(session=session):
        if privileges.get('edit'):
            cur_task = await get_task_data(task_id=task_id, session=session) 
            if title:
                cur_task['title'] = title
            if description:
                cur_task['description'] = description
            if priority:
                cur_task['priority'] = priority
            if status:
                cur_task['status'] = status
            cur_task.pop('id')
            cur_task.pop('creator_id')
            
            query = (update(task).where(task.c.id == task_id).values(**cur_task))
            await session.execute(query)
            await session.commit()
            
            return {'data': f'Task {task_id} updated successfully.'}
        else:
            return {'data': f'User {user.id} has no privileges for editing task {task_id}'}
    else:
        return {'data': f'No task with id - {task_id}'}
