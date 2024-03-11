import psycopg
from psycopg.rows import class_row

# Load up your config from somewhere...
from config import get_config

cfg = get_config()

conn = psycopg.connect(
    dbname=cfg.database_name,
    user=cfg.database_username,
    password=cfg.database_password,
    host=cfg.database_host,
)


def new_cursor(name=None, row_factory=None):
    if name is None:
        name = ""

    if row_factory is None:
        return conn.cursor(name=name)

    return conn.cursor(name=name, row_factory=class_row(row_factory))
