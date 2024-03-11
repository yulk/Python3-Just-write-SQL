from dataclasses import dataclass
import datetime
from typing import Optional


@dataclass
class User:
    id: int = None
    dt_created: datetime = None
    username: str = None
    email: str = None
    mobile: Optional[str] = None


create_sql = """
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    dt_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    username VARCHAR(100) NOT NULL,
    email VARCHAR(255),
    mobile VARCHAR(20)
);
"""
