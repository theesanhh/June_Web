import sys
from getpass import getpass

from sqlalchemy.exc import SQLAlchemyError

from backend.auth import MAX_PASSWORD_LENGTH, MIN_PASSWORD_LENGTH, set_admin_password
from backend.database import database_path, open_database


def main() -> None:
    if not sys.stdin.isatty():
        raise SystemExit('Mở PowerShell tương tác để nhập mật khẩu.')
    path = database_path()
    if not path.is_file():
        raise SystemExit('Chạy migration Alembic trước khi đặt mật khẩu.')

    password = getpass(f'Mật khẩu Admin ({MIN_PASSWORD_LENGTH}–{MAX_PASSWORD_LENGTH} ký tự): ')
    if password != getpass('Nhập lại mật khẩu: '):
        raise SystemExit('Hai lần nhập mật khẩu không khớp.')

    engine = open_database(path)
    try:
        set_admin_password(engine, password)
    except ValueError as error:
        raise SystemExit(str(error)) from None
    except SQLAlchemyError:
        raise SystemExit('Không thể lưu mật khẩu. Kiểm tra migration và quyền ghi SQLite.') from None
    finally:
        engine.dispose()
    print('Đã lưu mật khẩu Admin và thu hồi các phiên đăng nhập trước đó.')


if __name__ == '__main__':
    main()
