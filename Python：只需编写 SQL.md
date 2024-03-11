# Python：只需编写 SQL

2023 年 8 月 10 日


去年我写了很多 Go 代码。对于那些不熟悉的人来说，Go 更喜欢使用非 ORM、非查询构建器方法来与数据库交互。这是自然而然地归因于 sql 包：与数据库驱动程序一起使用的通用接口。即使在大型项目中，在 Go 中看到实际的 SQL 也是很常见的。

另一方面，Python的标准库中没有任何支持数据库交互的东西，这一直是社区需要解决的问题。 Python 有许多 ORM 和查询生成器：

- [SQLAlchemy SQL炼金术](https://www.sqlalchemy.org/)
- [Django ORM](https://docs.djangoproject.com/en/4.2/#the-model-layer)
- [Peewee](http://docs.peewee-orm.com/en/latest/)（我个人最喜欢的）
- ……还有更多！


当然，您可以使用您最喜欢的适配器并用 Python 编写 SQL（这就是我们要做的！），但我认为大多数开发人员都会同意，一旦您需要与数据库进行交互，它就远远不止如此。可能会立即使用像 SQLAlchemy 这样的 ORM。


（这并不是说 Go 没有流行的 ORM，但你更有可能看到 Go 开发人员利用标准库和数据库适配器，这是新 Go 开发人员将采用的典型方法。）


在这篇文章中，我的目标是像 Go 一样在 Python 中处理 SQL：

- 我想写SQL。
- 我不想依赖查询生成器（更不用说 ORM）。
- 我想将所有这些打包在一个抽象中，使我能够在数据库解决方案之间快速更改，并使其易于测试。
- 我希望我的数据库和业务逻辑之间有非常清晰的分离。

## 显示代码


我们将从一个典型的例子开始：

```python
# user/domain.py

@dataclass  
class User:  
	id: int = None  
	dt_created: datetime = None
	username: str = None
	email: str = None
	mobile: Optional[str] = None
```


`User` 是您可能看到的名为 `user` 的 SQL 表的字面定义。这包括我喜欢包含在所有 SQL 表中的一些列：

- `id` （主键）。
- `dt_created` 日期时间值，通常默认为 `NOW()` 。

所有字段默认为 `None` ，这将允许我们执行不包含表中所有列的 `SELECT` 查询，同时仍然能够将行转换为 `User` 对象。除了 `mobile` 之外，所有列都是 `NOT NULL` ，这里我使用 `Optional` 类型提示来强调该字段允许 `NULL` .

我们现在可以创建我们的存储库：

```python
# user/repository.py

from abc import ABC, abstractmethod

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
```


我喜欢我的存储库是抽象类，这可以确保任何未来的实现都需要遵循合同（尽可能使用 Python，最好的意图等等）。

我们的第一个实现是通过 [psycopg3]https://www.psycopg.org/psycopg3/docs/index.html) 实现PostgreSQL：

```python
# external/postgres.py

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
```

首先，我们设置连接。其次，返回 psycopg 游标的函数。 [custom row factories](https://www.psycopg.org/psycopg3/docs/advanced/rows.html) 包括自定义行工厂，我们很快就会看到这个功能有多么有用。

我们现在实现存储库：

```python
# user/repository.py
from external.postgres import conn, new_cursor

class UserPostgreSQL(UserRepository):
    def new(self, new_row: User) -> int:
        with new_cursor() as cur:
            cur.execute(
                """
            INSERT INTO user
            (username, email)
            VALUES
            (%s, %s)
            ON CONFLICT (email)
            DO NOTHING
            RETURNING id;
            """,
                (
                    new_row.username,
                    new_row.email
                ),
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
            FROM user
            WHERE id = %s
            """,
                (id_val,),
            )
            
            return cur.fetchone()
            
def new_user_repo() -> UserRepository:
    return UserPostgreSQL()
```


您会注意到 `new()` 使用基本游标，但 `get_by_id()` 使用带有类行工厂的游标，这意味着返回的行将是 `User` 类型。漂亮。


`new_user_repo()` 是我们在假设的业务逻辑中使用的函数，实现本身永远不会公开：

```python
from user.repository import *  
  
user_repo = new_user_repo()  
  
row = User()  
row.username = "joao"  
row.email = "joao@nospam.com"  
  
# Create a new record.  
new_id = user_repo.new(row)  
  
# Fetch the record we just created.  
new_row = user_repo.get_by_id(new_id)
# User(id=1, dt_created=datetime.datetime(2023, 8, 9, 23, 8, 14, 974074, tzinfo=datetime.timezone.utc), username='joao', email='joao@nospam.com', mobile=None)
```


`new_user_repo()` 可以修改为返回任何实现 `UserRepository` 的内容，可能是 MySQL 实现，也可能是 SQLite 实现，甚至可能是用于测试目的的模拟。

## 结论


我在技术上花了足够多的时间，看到语言和框架失宠，库和工具来来去去。 SQL 一直是一个常数，我看到了编写它的巨大好处。根据我的经验，任何能让您更接近数据库安装的事情（即使在云时代）都是一件好事。


上面的实现并没有突破任何新领域，事实上，它甚至可能看起来与 ORM API 非常相似……但这始终是我们的目标：编写原始 SQL 并不一定意味着非结构化代码。


我希望至少有一位 Python 开发人员在下次启动新项目时重新考虑他们的 SQL 方法。