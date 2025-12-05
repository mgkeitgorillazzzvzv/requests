from typing import List

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from models.tortoise import User
from models.pydantic import CreateUserRequest, UpdateUserRequest, UserOut, Token
from auth import (
	verify_password,
	get_password_hash,
	create_access_token,
	get_current_user,
	get_current_admin_user,
	get_current_admin_or_head_user,
)

router = APIRouter()


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


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
	user = await User.get_or_none(username=form_data.username)
	if not user or not verify_password(form_data.password, user.password):
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
	token_data = {"sub": user.username, "id": user.id, "role": (user.role if hasattr(user.role, 'value') else user.role)}
	access_token = create_access_token(token_data)
	return {"access_token": access_token, "token_type": "bearer"}


@router.post("/", response_model=UserOut)
async def create_user(payload: CreateUserRequest, current_user: User = Depends(get_current_admin_or_head_user)):
	
	from models.enums import Role
	if current_user.role == Role.HEAD:
		
		if payload.building != current_user.building:
			raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Head can only create users for their building")
	
	existing = await User.get_or_none(username=payload.username)
	if existing:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")
	hashed = get_password_hash(payload.password)
	user = await User.create(
		username=payload.username,
		password=hashed,
		first_name=payload.first_name,
		last_name=payload.last_name,
		role=payload.role,
		building=payload.building,
		department=payload.department,
	)
	return user_to_out(user)


@router.get("/", response_model=List[UserOut])
async def list_users(current_user: User = Depends(get_current_admin_or_head_user)):
	from models.enums import Role
	if current_user.role == Role.ADMIN:
		users = await User.all()
	else:  
		
		users = await User.filter(building=current_user.building)
	return [user_to_out(u) for u in users]


@router.get("/me", response_model=UserOut)
async def read_current_user(current_user: User = Depends(get_current_user)):
	return user_to_out(current_user)


@router.get("/{user_id}", response_model=UserOut)
async def read_user(user_id: int, admin: User = Depends(get_current_admin_user)):
	user = await User.get_or_none(id=user_id)
	if not user:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
	return user_to_out(user)


@router.patch("/{user_id}", response_model=UserOut)
async def update_user(
	user_id: int,
	payload: UpdateUserRequest,
	current_user: User = Depends(get_current_admin_or_head_user),
):
	user = await User.get_or_none(id=user_id)
	if not user:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

	from models.enums import Role
	
	if current_user.role == Role.HEAD:
		if user.building != current_user.building:
			raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Head can only update users from their building")

	update_data = payload.dict(exclude_unset=True)

	new_username = update_data.get("username")
	if new_username and new_username != user.username:
		existing = await User.get_or_none(username=new_username)
		if existing:
			raise HTTPException(
				status_code=status.HTTP_400_BAD_REQUEST,
				detail="Username already exists",
			)
		user.username = new_username

	if "first_name" in update_data:
		user.first_name = update_data["first_name"] or user.first_name
		
	if "last_name" in update_data:
		user.last_name = update_data["last_name"] or user.last_name

	if "role" in update_data and update_data["role"] is not None:
		user.role = update_data["role"]

	if "building" in update_data and update_data["building"] != user.building:
		if current_user.role != Role.ADMIN:
			raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin can change user building")
		user.building = update_data["building"]
		
	if "department" in update_data:
		user.department = update_data["department"]

	if "password" in update_data and update_data["password"]:
		user.password = get_password_hash(update_data["password"])

	await user.save()
	return user_to_out(user)


@router.delete("/{user_id}")
async def delete_user(user_id: int, admin: User = Depends(get_current_admin_user)):
	user = await User.get_or_none(id=user_id)
	if not user:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
	await user.delete()
	return {"detail": "deleted"}


