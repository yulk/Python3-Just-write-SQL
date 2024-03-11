# user/repository.py
from external.postgres import conn, new_cursor

from abc import ABC, abstractmethod

from user.domain import User


class UserRepository(ABC):
    @abstractmethod
    def new(self, new_row: User) -> int:
        """
        Create a new record and returns the new id value.
        """
        pass

    @abstractmethod
    def get_by_id(self, id_val: int) -> User:
        """
        Get a single record by ID value.
        """
        pass


class UserPostgreSQL(UserRepository):
    def new(self, new_row: User) -> int:
        with new_cursor() as cur:
            cur.execute(
                """
            INSERT INTO users
            (username, email)
            VALUES
            (%s, %s)
            RETURNING id;
            """,
                (new_row.username, new_row.email),
            )

            new_id = cur.fetchone()
            if new_id and len(new_id):
                conn.commit()
                new_id = new_id[0]
            else:
                new_id = 0

        return new_id

    def get_by_id(self, id_val: int) -> User:
        with new_cursor(name="get_by_id", row_factory=User) as cur:
            cur.execute(
                """
            SELECT *
            FROM users
            WHERE id = %s
            """,
                (id_val,),
            )

            return cur.fetchone()


def new_user_repo() -> UserRepository:
    return UserPostgreSQL()
