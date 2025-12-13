from models.pydantic import UserOut
from models.tortoise import User

def user_to_out(user: User) -> UserOut:
	return UserOut(
		id=user.id,
		username=user.username,
		first_name=user.first_name,
		last_name=user.last_name,
		role=(user.role if hasattr(user.role, 'value') else user.role),
		building=user.building,
		department=user.department,
	)
