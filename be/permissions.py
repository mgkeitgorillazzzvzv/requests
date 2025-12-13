


from typing import Optional
from fastapi import HTTPException, status
from models.tortoise import User, Request, RequestPhoto
from models.enums import Role


class PermissionDenied(HTTPException):
    
    def __init__(self, detail: str = "Access denied"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


def normalize_role(role) -> Role:
    
    if hasattr(role, "value"):
        return role
    return Role(role) if isinstance(role, str) else role


def is_admin(user: User) -> bool:
    
    try:
        role = normalize_role(user.role)
        return role == Role.ADMIN
    except Exception:
        return False


def is_head(user: User) -> bool:
    
    try:
        role = normalize_role(user.role)
        return role == Role.HEAD
    except Exception:
        return False


def is_specialist(user: User) -> bool:
    
    try:
        role = normalize_role(user.role)
        return role == Role.SPECIALIST
    except Exception:
        return False


def is_executor(user: User) -> bool:
    
    try:
        role = normalize_role(user.role)
        return role == Role.EXECUTOR
    except Exception:
        return False


def is_admin_or_head(user: User) -> bool:
    
    return is_admin(user) or is_head(user)


def can_access_building(user: User, building) -> bool:
    




    if is_admin(user):
        return True
    return user.building == building


def can_access_department(user: User, department: Optional[str]) -> bool:
    




    if is_admin(user) or is_head(user):
        return True
    if user.department is None:
        return True  
    return user.department == department


def can_view_request(user: User, request: Request) -> bool:
    





    if is_admin(user):
        return True
    
    if is_head(user):
        return request.building == user.building
    
    if is_specialist(user) or is_executor(user):
        if request.building != user.building:
            return False
        if user.department and request.department != user.department:
            return False
        return True
    
    return False


def can_edit_request(user: User, request: Request) -> bool:
    





    if is_admin(user):
        return True
    
    if is_head(user):
        return request.building == user.building
    
    if is_specialist(user):
        return (request.building == user.building and 
                (not user.department or request.department == user.department))
    
    return False


def can_delete_request(user: User, request: Request) -> bool:
    




    if is_admin(user):
        return True
    
    if is_head(user):
        return request.building == user.building
    
    return False


def can_change_request_building(user: User) -> bool:
    



    return is_admin(user)


def can_create_request_in_building(user: User, building) -> bool:
    




    if is_admin(user):
        return True
    
    if is_head(user) or is_specialist(user):
        return building == user.building
    
    return False


def can_request_status_change(user: User, request: Request) -> bool:
    



    if not (is_executor(user) or is_specialist(user)):
        return False
    
    if request.building != user.building:
        return False
    
    if user.department and request.department != user.department:
        return False
    
    return True


def can_review_status_change(user: User, request: Request) -> bool:
    



    if is_admin(user):
        return True
    
    if is_head(user):
        return request.building == user.building
    
    return False


def can_directly_change_status(user: User, request: Request) -> bool:
    



    if is_admin(user):
        return True
    
    if is_head(user):
        return request.building == user.building
    
    return False


def can_upload_photo_to_request(user: User, request: Request) -> bool:
    





    if is_admin(user):
        return True
    
    if is_head(user):
        return request.building == user.building
    
    if is_specialist(user) or is_executor(user):
        if request.building != user.building:
            return False
        if user.department and request.department != user.department:
            return False
        return True
    
    return False


def can_delete_photo(user: User, request: Request) -> bool:
    




    if is_admin(user):
        return True
    
    if is_head(user):
        return request.building == user.building
    
    return False


def can_approve_anonymous_request(user: User, request: Request) -> bool:
    




    if not request.is_anonymous:
        return False
    
    if is_admin(user):
        return True
    
    if is_head(user):
        return request.building == user.building
    
    return False


def can_create_user(user: User) -> bool:
    




    return is_admin(user) or is_head(user)


def can_create_user_in_building(user: User, building) -> bool:
    




    if is_admin(user):
        return True
    
    if is_head(user):
        return building == user.building
    
    return False


def can_update_user(user: User, target_user: User) -> bool:
    




    if is_admin(user):
        return True
    
    if is_head(user):
        return target_user.building == user.building
    
    return False


def can_delete_user(user: User) -> bool:
    



    return is_admin(user)


def require_view_access(user: User, request: Request):
    
    if not can_view_request(user, request):
        raise PermissionDenied("Not authorized to view this request")


def require_edit_access(user: User, request: Request):
    
    if not can_edit_request(user, request):
        raise PermissionDenied("Not authorized to edit this request")


def require_delete_access(user: User, request: Request):
    
    if not can_delete_request(user, request):
        raise PermissionDenied("Not authorized to delete this request")


def require_admin(user: User):
    
    if not is_admin(user):
        raise PermissionDenied("Administrator access required")


def require_admin_or_head(user: User):
    
    if not is_admin_or_head(user):
        raise PermissionDenied("Administrator or head of department access required")
