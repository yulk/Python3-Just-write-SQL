from user.repository import new_user_repo
from user.domain import User

user_repo = new_user_repo()

row = User()
row.username = "joao"
row.email = "joao@nospam.com"

# Create a new record.
new_id = user_repo.new(row)
print(new_id)
# Fetch the record we just created.
new_row = user_repo.get_by_id(new_id)
print(new_row)
