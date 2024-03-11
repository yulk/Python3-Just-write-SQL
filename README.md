# 中文版Python: Just write SQL
含实例的完整代码

https://joaodlf.com/python-just-write-sql

## 数据库表创建sql
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    dt_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    username VARCHAR(100) NOT NULL,
    email VARCHAR(255),
    mobile VARCHAR(20)
);
```
