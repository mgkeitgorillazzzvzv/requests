from pydantic import BaseModel
from models.enums import Building, Role, RequestStatus


class CreateUserRequest(BaseModel):
    username: str
    password: str
    first_name: str
    last_name: str
    role: Role
    building: Building | None = None
    department: str | None = None


class UpdateUserRequest(BaseModel):
    username: str | None = None
    password: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    role: Role | None = None
    building: Building | None = None
    department: str | None = None

class CreateRequestRequest(BaseModel): 
    title: str
    description: str | None = None
    building: Building
    department: str | None = None
    status: RequestStatus = RequestStatus.CREATED
    urgent: bool = False


class UpdateRequestRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    building: Building | None = None
    department: str | None = None
    urgent: bool | None = None


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    id: int | None = None
    username: str | None = None
    role: Role | None = None


class PhotoUpload(BaseModel):
    caption: str | None = None
    order: int = 0


class PhotoOut(BaseModel):
    id: int
    file_path: str
    caption: str | None = None
    order: int
    uploaded_at: str  

    class Config:
        from_attributes = True


class UserOut(BaseModel):
    id: int
    username: str
    first_name: str
    last_name: str
    role: Role
    building: Building | None = None
    department: str | None = None

    class Config:
        from_attributes = True

class RequestOut(BaseModel):
    id: int
    status: RequestStatus
    title: str
    description: str | None = None
    building: Building
    opened_by_id: int
    closed_by_id: int | None = None
    opened_by: UserOut
    closed_by: UserOut | None = None
    opened_at: str  
    closed_at: str | None = None  
    department: str | None = None
    urgent: bool = False
    photos: list[PhotoOut] = []
    history: list["RequestHistoryOut"] = []
    pending_status_changes: list["StatusChangeRequestOut"] = []

    class Config:
        from_attributes = True


class StatsOut(BaseModel):
    total_requests: int
    open_requests: int
    closed_requests: int
    ratio: float
    avg_processing_time_hours: float


class CreateStatusChangeRequest(BaseModel):
    requested_status: RequestStatus  
    reason: str | None = None  
    photo_id: int | None = None  


class ReviewStatusChangeRequest(BaseModel):
    approved: bool
    rejection_reason: str | None = None
    rejection_photo_id: int | None = None


class StatusChangeRequestOut(BaseModel):
    id: int
    request_id: int
    requested_by: UserOut
    requested_status: RequestStatus
    reason: str | None = None
    photo: PhotoOut | None = None
    created_at: str
    reviewed_at: str | None = None
    reviewed_by: UserOut | None = None
    approved: bool | None = None
    rejection_reason: str | None = None
    rejection_photo: PhotoOut | None = None

    class Config:
        from_attributes = True


class RequestHistoryOut(BaseModel):
    id: int
    request_id: int
    action: str
    performed_by: UserOut
    old_status: RequestStatus | None = None
    new_status: RequestStatus | None = None
    details: str | None = None
    created_at: str

    class Config:
        from_attributes = True