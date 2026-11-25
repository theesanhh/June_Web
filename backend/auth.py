import hashlib
import logging
import re
import secrets
import time
from collections.abc import Iterator
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, SecretStr
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

router = APIRouter(prefix='/api/admin', tags=['admin'])
COOKIE_NAME = 'june_admin_session'
SESSION_SECONDS = 8 * 60 * 60
MIN_PASSWORD_LENGTH = 12
MAX_PASSWORD_LENGTH = 128
NO_CACHE = {'Cache-Control': 'no-store'}
TOKEN_PATTERN = re.compile(r'[A-Za-z0-9_-]{43}')
logger = logging.getLogger('uvicorn.error')


class Login(BaseModel):
    password: SecretStr


class SessionStatus(BaseModel):
    configured: bool
    authenticated: bool


def derive_password(password: str, salt: bytes) -> str:
    return hashlib.scrypt(
        password.encode('utf-8'), salt=salt, n=2**17, r=8, p=1,
        maxmem=256 * 1024 * 1024, dklen=32,
    ).hex()


def set_admin_password(engine: Engine, password: str) -> None:
    if not MIN_PASSWORD_LENGTH <= len(password) <= MAX_PASSWORD_LENGTH:
        raise ValueError(f'Mật khẩu phải dài từ {MIN_PASSWORD_LENGTH} đến {MAX_PASSWORD_LENGTH} ký tự.')
    salt = secrets.token_bytes(16)
    stored_hash = f'{salt.hex()}:{derive_password(password, salt)}'
    with engine.begin() as conn:
        conn.execute(text('''
            INSERT INTO admin_account (id, password_hash) VALUES (1, :password_hash)
            ON CONFLICT (id) DO UPDATE SET password_hash = excluded.password_hash
        '''), {'password_hash': stored_hash})
        conn.execute(text('DELETE FROM admin_sessions'))


def session_digest(token: str) -> str:
    return hashlib.sha256(token.encode('ascii')).hexdigest()


def request_session_digest(request: Request) -> str | None:
    token = request.cookies.get(COOKIE_NAME, '')
    return session_digest(token) if TOKEN_PATTERN.fullmatch(token) else None


def auth_database(request: Request) -> Iterator[Engine]:
    if request.url.hostname not in {'localhost', '127.0.0.1', '::1'}:
        raise HTTPException(status_code=403, detail='Chỉ hỗ trợ đăng nhập local.', headers=NO_CACHE)
    origin = request.headers.get('origin')
    if origin is not None and origin != f'{request.url.scheme}://{request.url.netloc}':
        raise HTTPException(status_code=403, detail='Nguồn yêu cầu không hợp lệ.', headers=NO_CACHE)
    try:
        if request.app.state.db_path.is_file():
            yield request.app.state.engine
            return
    except SQLAlchemyError as error:
        logger.warning('Admin database unavailable (%s).', type(error).__name__)
    raise HTTPException(status_code=503, detail='Cơ sở dữ liệu chưa sẵn sàng.', headers=NO_CACHE)


AuthDatabase = Annotated[Engine, Depends(auth_database)]


@router.get('/session')
def get_session(request: Request, response: Response, engine: AuthDatabase) -> SessionStatus:
    response.headers.update(NO_CACHE)
    digest = request_session_digest(request)
    with engine.connect() as conn:
        configured = conn.execute(text('SELECT 1 FROM admin_account WHERE id = 1')).scalar() == 1
        authenticated = configured and digest is not None and conn.execute(text('''
            SELECT 1 FROM admin_sessions WHERE token_hash = :digest AND expires_at > :now
        '''), {'digest': digest, 'now': int(time.time())}).scalar() == 1
    return SessionStatus(configured=configured, authenticated=authenticated)


@router.post('/session')
def login(payload: Login, request: Request, response: Response, engine: AuthDatabase) -> SessionStatus:
    password = payload.password.get_secret_value()
    with engine.connect() as conn:
        stored = conn.execute(text('SELECT password_hash FROM admin_account WHERE id = 1')).scalar_one_or_none()

    if stored is None:
        raise HTTPException(status_code=409, detail='Admin chưa có mật khẩu.', headers=NO_CACHE)
    salt, expected = stored.split(':', maxsplit=1)
    if not MIN_PASSWORD_LENGTH <= len(password) <= MAX_PASSWORD_LENGTH or not secrets.compare_digest(
        derive_password(password, bytes.fromhex(salt)), expected,
    ):
        raise HTTPException(status_code=401, detail='Mật khẩu không đúng.', headers=NO_CACHE)

    token = secrets.token_urlsafe(32)
    now = int(time.time())
    old_digest = request_session_digest(request)
    with engine.begin() as conn:
        inserted = conn.execute(text('''
            INSERT INTO admin_sessions (token_hash, expires_at)
            SELECT :digest, :expires FROM admin_account WHERE id = 1 AND password_hash = :stored
        '''), {'digest': session_digest(token), 'expires': now + SESSION_SECONDS, 'stored': stored})
        if inserted.rowcount != 1:
            raise HTTPException(status_code=401, detail='Mật khẩu đã thay đổi.', headers=NO_CACHE)
        conn.execute(text('DELETE FROM admin_sessions WHERE expires_at <= :now OR token_hash = :old'),
                     {'now': now, 'old': old_digest})

    response.headers.update(NO_CACHE)
    response.set_cookie(COOKIE_NAME, token, max_age=SESSION_SECONDS, path='/api',
                        httponly=True, samesite='strict', secure=request.url.scheme == 'https')
    return SessionStatus(configured=True, authenticated=True)


@router.delete('/session', status_code=204)
def logout(request: Request, engine: AuthDatabase) -> Response:
    digest = request_session_digest(request)
    if digest is not None:
        with engine.begin() as conn:
            conn.execute(text('DELETE FROM admin_sessions WHERE token_hash = :digest'), {'digest': digest})
    response = Response(status_code=204, headers=NO_CACHE)
    response.delete_cookie(COOKIE_NAME, path='/api', httponly=True, samesite='strict',
                           secure=request.url.scheme == 'https')
    return response
