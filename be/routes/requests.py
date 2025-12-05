import os
import uuid
import io
import asyncio
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import FileResponse, Response
from PIL import Image, ExifTags
from auth import get_current_user
from models.enums import RequestStatus, Role, Building
from models.tortoise import Request, User, RequestPhoto, RequestStatusChangeRequest, RequestHistory
from models.pydantic import (
    CreateRequestRequest,
    CreateAnonymousRequestRequest,
    UpdateRequestRequest,
    RequestOut,
    PhotoOut,
    CreateStatusChangeRequest,
    ReviewStatusChangeRequest,
    StatusChangeRequestOut,
    RequestHistoryOut,
    UserOut,
    PaginatedRequestsOut,
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

async def create_history_entry(
    request: Request,
    action: str,
    user: User,
    old_status: RequestStatus | None = None,
    new_status: RequestStatus | None = None,
    details: str | None = None
):
    """Helper to create history entry"""
    await RequestHistory.create(
        request=request,
        action=action,
        performed_by=user,
        old_status=old_status,
        new_status=new_status,
        details=details
    )

async def request_to_out(request: Request) -> RequestOut:

    if not hasattr(request, '_fetched_related') or 'photos' not in getattr(request, '_fetched_related', []):
        await request.fetch_related('photos')
    if not hasattr(request, '_fetched_related') or 'opened_by' not in getattr(request, '_fetched_related', []):
        await request.fetch_related('opened_by')
    if request.closed_by_id and (not hasattr(request, '_fetched_related') or 'closed_by' not in getattr(request, '_fetched_related', [])):
        await request.fetch_related('closed_by')


    history_entries = await RequestHistory.filter(request=request).prefetch_related('performed_by').order_by('-created_at')
    history_list = []
    for entry in history_entries:
        history_list.append(RequestHistoryOut(
            id=entry.id,
            request_id=entry.request_id,
            action=entry.action,
            performed_by=user_to_out(entry.performed_by),
            old_status=entry.old_status, 
            new_status=entry.new_status,
            details=entry.details,
            created_at=entry.created_at.isoformat()
        ))


    pending_changes = await RequestStatusChangeRequest.filter(
        request=request,
        approved__isnull=True
    ).prefetch_related('requested_by', 'reviewed_by', 'photo', 'rejection_photo')

    pending_list = []
    for change in pending_changes:
        photo_out = None
        if change.photo:
            photo_out = PhotoOut(
                id=change.photo.id,
                file_path=change.photo.file_path,
                caption=change.photo.caption,
                order=change.photo.order,
                uploaded_at=change.photo.uploaded_at.isoformat()
            )

        rejection_photo_out = None
        if change.rejection_photo:
            rejection_photo_out = PhotoOut(
                id=change.rejection_photo.id,
                file_path=change.rejection_photo.file_path,
                caption=change.rejection_photo.caption,
                order=change.rejection_photo.order,
                uploaded_at=change.rejection_photo.uploaded_at.isoformat()
            )

        reviewed_by_out = None
        if change.reviewed_by:
            reviewed_by_out = user_to_out(change.reviewed_by)

        pending_list.append(StatusChangeRequestOut(
            id=change.id,
            request_id=change.request_id,
            requested_by=user_to_out(change.requested_by),
            requested_status=change.requested_status,
            reason=change.reason,
            photo=photo_out,
            created_at=change.created_at.isoformat(),
            reviewed_at=change.reviewed_at.isoformat() if change.reviewed_at else None,
            reviewed_by=reviewed_by_out,
            approved=change.approved,
            rejection_reason=change.rejection_reason,
            rejection_photo=rejection_photo_out
        ))

    photos_list = [
        PhotoOut(
            id=photo.id,
            file_path=photo.file_path,
            caption=photo.caption,
            order=photo.order,
            uploaded_at=photo.uploaded_at.isoformat()
        )
        for photo in (request.photos if hasattr(request, 'photos') else [])
    ]

    opened_by_out = user_to_out(request.opened_by) if request.opened_by else None

    closed_by_out = None
    if request.closed_by:
        closed_by_out = user_to_out(request.closed_by)

    return RequestOut(
        id=request.id,
        status=(request.status if hasattr(request.status, 'value') else request.status),
        title=request.title,
        description=request.description,
        building=(request.building if hasattr(request.building, 'value') else request.building),
        opened_by_id=request.opened_by_id,
        closed_by_id=request.closed_by_id,
        opened_by=opened_by_out,
        closed_by=closed_by_out,
        opened_at=request.opened_at.isoformat(),
        closed_at=request.closed_at.isoformat() if request.closed_at else None,
        department=request.department,
        urgent=request.urgent,
        is_anonymous=request.is_anonymous,
        photos=photos_list,
        history=history_list,
        pending_status_changes=pending_list,
    )

@router.post("/")
async def create_request(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    building: Building = Form(...),
    department: Optional[str] = Form(None),
    status: RequestStatus = Form(RequestStatus.CREATED),
    urgent: bool = Form(False),
    photos: List[UploadFile] = File(None),
    user: User = Depends(get_current_user)
) -> RequestOut:


    if user.role == Role.ADMIN:
        pass
    elif user.role == Role.HEAD:
        if building != user.building:
            raise HTTPException(status_code=403, detail="Heads can only create requests in their building")
    elif user.role == Role.SPECIALIST:
        if building != user.building:
            raise HTTPException(status_code=403, detail="Specialists can only create requests in their building")

        if user.department:
            department = user.department
        else:
            raise HTTPException(status_code=400, detail="Specialist must have a department assigned")
    else:
        raise HTTPException(status_code=403, detail="Not authorized to create requests")

    request = await Request.create(
        title=title,
        description=description,
        building=building,
        department=department,
        status=status,
        urgent=urgent,
        opened_by_id=user.id,
    )


    await create_history_entry(
        request=request,
        action="created",
        user=user,
        new_status=status,
        details=f"Request created by {user.first_name} {user.last_name}"
    )


    from routes.notifications import notify_request_created
    import asyncio
    asyncio.create_task(notify_request_created(request, user))


    if photos:
        for idx, photo in enumerate(photos):
            if photo and photo.filename:

                if photo.content_type not in ["image/jpeg", "image/png", "image/jpg", "image/webp"]:
                    continue


                file_path = save_upload_file(photo)


                await RequestPhoto.create(
                    request_id=request.id,
                    file_path=file_path,
                    caption=None,
                    order=idx
                )


    # if department:
    #     from routes.notifications import notify_department_employees, NotificationPayload
    #     payload = NotificationPayload(
    #         title=f"Новая заявка {department}",
    #         body=f"{title}",
    #         data={
    #             "url": f"/requests/{request.id}",
    #             "requestId": request.id
    #         }
    #     )




    request = await Request.filter(id=request.id).prefetch_related('opened_by', 'closed_by', 'photos').first()
    return await request_to_out(request)


@router.post("/anonymous")
async def create_anonymous_request(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    building: Building = Form(...),
    department: Optional[str] = Form(None),
    photos: List[UploadFile] = File(None),
) -> RequestOut:
    """Создание анонимной заявки без авторизации. Попадает в статус PENDING_CREATION_APPROVAL"""
    
    request = await Request.create(
        title=title,
        description=description,
        building=building,
        department=department,
        status=RequestStatus.PENDING_CREATION_APPROVAL,
        urgent=False,
        opened_by_id=None,
        is_anonymous=True
    )

    if photos:
        for idx, photo in enumerate(photos):
            if photo and photo.filename:
                if photo.content_type not in ["image/jpeg", "image/png", "image/jpg", "image/webp"]:
                    continue
                
                file_path = save_upload_file(photo)
                
                await RequestPhoto.create(
                    request_id=request.id,
                    file_path=file_path,
                    caption=None,
                    order=idx
                )

    request = await Request.filter(id=request.id).prefetch_related('opened_by', 'closed_by', 'photos').first()
    return await request_to_out(request)


@router.post("/{request_id}/approve-anonymous")
async def approve_anonymous_request(
    request_id: int,
    user: User = Depends(get_current_user)
) -> RequestOut:
    """Хед апрувает анонимную заявку и переводит её в статус CREATED"""
    request = await Request.get_or_none(id=request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    if not request.is_anonymous:
        raise HTTPException(status_code=400, detail="This request is not anonymous")
    
    if request.status != RequestStatus.PENDING_CREATION_APPROVAL:
        raise HTTPException(status_code=400, detail="Request is not pending approval")
    
    # Проверяем права доступа
    if user.role == Role.ADMIN:
        pass
    elif user.role == Role.HEAD:
        if request.building != user.building:
            raise HTTPException(status_code=403, detail="Not authorized to approve this request")
    else:
        raise HTTPException(status_code=403, detail="Only heads and admins can approve anonymous requests")
    
    old_status = request.status
    request.status = RequestStatus.CREATED
    request.opened_by_id = user.id  # Хед становится автором заявки
    await request.save()
    
    # Создаем запись в истории
    await create_history_entry(
        request=request,
        action="anonymous_request_approved",
        user=user,
        old_status=old_status,
        new_status=RequestStatus.CREATED,
        details=f"Анонимная заявка одобрена {user.first_name} {user.last_name}"
    )
    
    request = await Request.filter(id=request_id).prefetch_related('opened_by', 'closed_by', 'photos').first()
    return await request_to_out(request)


@router.get("/")
async def list_requests(
    user: User = Depends(get_current_user),
    building: Optional[Building] = None,
    status: Optional[RequestStatus] = None,
    search: Optional[str] = None,
    offset: int = 0,
    limit: int = 6
) -> PaginatedRequestsOut:

    if user.role == Role.ADMIN:
        query = Request.filter(building=building) if building else Request.all()
    elif user.role == Role.HEAD:
        query = Request.filter(building=user.building)
    elif user.role in (Role.SPECIALIST, Role.EXECUTOR):

        if user.building and user.department:
            query = Request.filter(building=user.building, department=user.department)
        elif user.building:
            query = Request.filter(building=user.building)
        else:
            query = Request.none()
    else:
        return PaginatedRequestsOut(items=[], total=0, offset=offset, limit=limit, has_more=False)

    if status:
        query = query.filter(status=status)

    # Search filter
    if search:
        from tortoise.expressions import Q
        search_term = f"%{search}%"
        query = query.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(department__icontains=search) |
            Q(opened_by__first_name__icontains=search) |
            Q(opened_by__last_name__icontains=search)
        )

    total = await query.count()

    requests = await query.order_by('-urgent', '-opened_at').offset(offset).limit(limit).prefetch_related('opened_by', 'closed_by', 'photos')

    items = [await request_to_out(request) for request in requests]
    has_more = offset + len(items) < total

    return PaginatedRequestsOut(
        items=items,
        total=total,
        offset=offset,
        limit=limit,
        has_more=has_more
    )



@router.get("/{request_id}")
async def get_request(request_id: int, user: User = Depends(get_current_user)) -> RequestOut:
    request = await Request.filter(id=request_id).prefetch_related('opened_by', 'closed_by', 'photos').first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")

    if user.role == Role.ADMIN:
        return await request_to_out(request)

    if user.role == Role.HEAD:
        if request.building != user.building:
            raise HTTPException(status_code=403, detail="Not authorized to view this request")
        return await request_to_out(request)

    if user.role == Role.SPECIALIST:
        if request.building != user.building:
            raise HTTPException(status_code=403, detail="Not authorized to view this request")
        if user.department and request.department != user.department:
            raise HTTPException(status_code=403, detail="Not authorized to view this request")
        return await request_to_out(request)

    if user.role == Role.EXECUTOR:
        if request.building != user.building:
            raise HTTPException(status_code=403, detail="Not authorized to view this request")
        if user.department and request.department != user.department:
            raise HTTPException(status_code=403, detail="Not authorized to view this request")
        return await request_to_out(request)

    raise HTTPException(status_code=403, detail="Not authorized to view this request")

@router.delete("/{request_id}")
async def delete_request(request_id: int, user: User = Depends(get_current_user)):
    request = await Request.get_or_none(id=request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    if user.role == Role.ADMIN:
        pass
    elif user.role == Role.HEAD:
        if request.building != user.building:
            raise HTTPException(status_code=403, detail="Not authorized to delete this request")
    else:
        raise HTTPException(status_code=403, detail="Not authorized to delete this request")
    await request.delete()
    return {"detail": "Request deleted"}

@router.patch("/{request_id}")
async def update_request(request_id: int, payload: UpdateRequestRequest, user: User = Depends(get_current_user)) -> RequestOut:
    request = await Request.get_or_none(id=request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    if user.role not in (Role.ADMIN, Role.HEAD):
        raise HTTPException(status_code=403, detail="Not authorized to update this request")
    if user.role == Role.HEAD and request.building != user.building:
        raise HTTPException(status_code=403, detail="Not authorized to update this request")

    if payload.title is not None and payload.title != request.title:
        request.title = payload.title
    if payload.description is not None and payload.description != request.description:
        request.description = payload.description
    if payload.building is not None and payload.building != request.building:
        if user.role != Role.ADMIN:
            raise HTTPException(status_code=403, detail="Only admin can change request building")
        request.building = payload.building
    if payload.department is not None and payload.department != request.department:
        request.department = payload.department
    if payload.urgent is not None and payload.urgent != request.urgent:
        request.urgent = payload.urgent
    await request.save()
    await request.fetch_related('opened_by', 'closed_by', 'photos')
    return await request_to_out(request)


@router.put("/{request_id}/status")
async def update_request_status(request_id: int, status: RequestStatus, user: User = Depends(get_current_user)):
    """DEPRECATED: Use status change requests instead. This is kept for direct admin/head changes only."""
    request = await Request.get_or_none(id=request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")


    if user.role == Role.ADMIN:
        allowed = True
    elif user.role == Role.HEAD:
        allowed = user.building == request.building
    else:
        raise HTTPException(status_code=403, detail="Not authorized. Use status change requests instead.")

    if not allowed:
        raise HTTPException(status_code=403, detail="Not authorized to update this request")

    old_status = request.status
    request.status = status
    if status in (RequestStatus.COMPLETED, RequestStatus.POSTPONED):
        from datetime import datetime
        request.closed_by_id = user.id
        request.closed_at = datetime.utcnow()
    await request.save()


    await create_history_entry(
        request=request,
        action="status_changed",
        user=user,
        old_status=old_status,
        new_status=status,
        details=f"Status directly changed by {user.first_name} {user.last_name}"
    )

    await request.fetch_related('opened_by', 'closed_by', 'photos')
    return await request_to_out(request)



@router.post("/{request_id}/status-change-request")
async def create_status_change_request(
    request_id: int,
    payload: CreateStatusChangeRequest,
    user: User = Depends(get_current_user)
) -> StatusChangeRequestOut:
    """Executor or Specialist creates a request to change status (to COMPLETED or POSTPONED)"""
    request = await Request.get_or_none(id=request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")


    if user.role not in (Role.EXECUTOR, Role.SPECIALIST):
        raise HTTPException(status_code=403, detail="Only executors and specialists can create status change requests")


    if request.building != user.building:
        raise HTTPException(status_code=403, detail="Not authorized for this building")
    if user.department and request.department != user.department:
        raise HTTPException(status_code=403, detail="Not authorized for this department")


    if payload.requested_status == RequestStatus.COMPLETED:
        if not payload.photo_id:
            raise HTTPException(status_code=400, detail="Photo is required for COMPLETED status")

        photo = await RequestPhoto.get_or_none(id=payload.photo_id, request_id=request_id)
        if not photo:
            raise HTTPException(status_code=404, detail="Photo not found or doesn't belong to this request")
    elif payload.requested_status == RequestStatus.POSTPONED:
        if not payload.reason:
            raise HTTPException(status_code=400, detail="Reason is required for POSTPONED status")
    else:
        raise HTTPException(status_code=400, detail="Can only request COMPLETED or POSTPONED status")


    change_request = await RequestStatusChangeRequest.create(
        request=request,
        requested_by=user,
        requested_status=payload.requested_status,
        reason=payload.reason,
        photo_id=payload.photo_id
    )


    old_status = request.status
    request.status = RequestStatus.PENDING_APPROVAL
    await request.save()


    await create_history_entry(
        request=request,
        action="status_change_requested",
        user=user,
        old_status=old_status,
        new_status=RequestStatus.PENDING_APPROVAL,
        details=f"{user.first_name} {user.last_name} requested status change to {payload.requested_status.value}"
    )


    from routes.notifications import notify_status_change_requested
    import asyncio
    asyncio.create_task(notify_status_change_requested(request, user))


    await change_request.fetch_related('requested_by', 'photo')

    photo_out = None
    if change_request.photo:
        photo_out = PhotoOut(
            id=change_request.photo.id,
            file_path=change_request.photo.file_path,
            caption=change_request.photo.caption,
            order=change_request.photo.order,
            uploaded_at=change_request.photo.uploaded_at.isoformat()
        )

    return StatusChangeRequestOut(
        id=change_request.id,
        request_id=change_request.request_id,
        requested_by=user_to_out(change_request.requested_by),
        requested_status=change_request.requested_status,
        reason=change_request.reason,
        photo=photo_out,
        created_at=change_request.created_at.isoformat(),
        reviewed_at=None,
        reviewed_by=None,
        approved=None,
        rejection_reason=None,
        rejection_photo=None
    )


@router.post("/{request_id}/status-change-request/{change_request_id}/review")
async def review_status_change_request(
    request_id: int,
    change_request_id: int,
    payload: ReviewStatusChangeRequest,
    user: User = Depends(get_current_user)
) -> RequestOut:
    """Head of department reviews and approves/rejects a status change request"""
    request = await Request.get_or_none(id=request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")

    change_request = await RequestStatusChangeRequest.get_or_none(id=change_request_id, request_id=request_id)
    if not change_request:
        raise HTTPException(status_code=404, detail="Status change request not found")


    if user.role not in (Role.HEAD, Role.ADMIN):
        raise HTTPException(status_code=403, detail="Only head of department can review status change requests")


    if request.building != user.building and user.role != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized for this building")


    if change_request.approved is not None:
        raise HTTPException(status_code=400, detail="This request has already been reviewed")

    from datetime import datetime
    change_request.reviewed_at = datetime.utcnow()
    change_request.reviewed_by = user
    change_request.approved = payload.approved

    if payload.approved:

        old_status = request.status
        request.status = change_request.requested_status
        if change_request.requested_status in (RequestStatus.COMPLETED, RequestStatus.POSTPONED):

            request.closed_by_id = change_request.requested_by_id
            request.closed_at = datetime.utcnow()
        await request.save()


        await create_history_entry(
            request=request,
            action="status_change_approved",
            user=user,
            old_status=old_status,
            new_status=change_request.requested_status,
            details=f"{user.first_name} {user.last_name} approved status change to {change_request.requested_status.value}"
        )


        from routes.notifications import notify_status_change_approved
        import asyncio
        asyncio.create_task(notify_status_change_approved(request, change_request.requested_status))
    else:

        change_request.rejection_reason = payload.rejection_reason
        if payload.rejection_photo_id:

            photo = await RequestPhoto.get_or_none(id=payload.rejection_photo_id, request_id=request_id)
            if photo:
                change_request.rejection_photo_id = payload.rejection_photo_id


        old_status = request.status
        request.status = RequestStatus.CREATED
        await request.save()


        details = f"{user.first_name} {user.last_name} rejected status change request"
        if payload.rejection_reason:
            details += f": {payload.rejection_reason}"

        await create_history_entry(
            request=request,
            action="status_change_rejected",
            user=user,
            old_status=old_status,
            new_status=RequestStatus.CREATED,
            details=details
        )


        from routes.notifications import notify_status_change_rejected
        import asyncio
        asyncio.create_task(notify_status_change_rejected(
            request,
            change_request.requested_by,
            payload.rejection_reason
        ))

    await change_request.save()


    request = await Request.filter(id=request_id).prefetch_related('opened_by', 'closed_by', 'photos').first()
    return await request_to_out(request)



UPLOAD_DIR = "uploads/photos"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def save_upload_file(upload_file: UploadFile) -> str:
    """Save uploaded file and return file path"""
    file_extension = os.path.splitext(upload_file.filename)[1] if upload_file.filename else ".jpg"
    filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    with open(file_path, "wb") as buffer:
        content = upload_file.file.read()
        buffer.write(content)

    return file_path


@router.post("/{request_id}/photos", response_model=PhotoOut)
async def upload_photo(
    request_id: int,
    file: UploadFile = File(...),
    caption: Optional[str] = Form(None),
    order: int = Form(0),
    user: User = Depends(get_current_user)
):

    request = await Request.get_or_none(id=request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")


    if user.role == Role.ADMIN:
        pass
    elif user.role == Role.HEAD:
        if request.building != user.building:
            raise HTTPException(status_code=403, detail="Not authorized to upload to this request")
    elif user.role in (Role.SPECIALIST, Role.EXECUTOR):
        if request.building != user.building:
            raise HTTPException(status_code=403, detail="Not authorized to upload to this request")


        if user.department and request.department != user.department:
            raise HTTPException(status_code=403, detail="Not authorized to upload to this request")
    else:
        raise HTTPException(status_code=403, detail="Not authorized to upload to this request")


    if file.content_type not in ["image/jpeg", "image/png", "image/jpg", "image/webp"]:
        raise HTTPException(status_code=400, detail="Only image files are allowed")


    file_path = save_upload_file(file)


    photo = await RequestPhoto.create(
        request_id=request_id,
        file_path=file_path,
        caption=caption,
        order=order
    )

    return PhotoOut(
        id=photo.id,
        file_path=photo.file_path,
        caption=photo.caption,
        order=photo.order,
        uploaded_at=photo.uploaded_at.isoformat()
    )


@router.get("/{request_id}/photos", response_model=List[PhotoOut])
async def get_request_photos(request_id: int, user: User = Depends(get_current_user)):

    request = await Request.get_or_none(id=request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")


    if user.role == Role.ADMIN:
        pass
    elif user.role == Role.HEAD:
        if request.building != user.building:
            raise HTTPException(status_code=403, detail="Not authorized to view this request")
    elif user.role == Role.SPECIALIST:
        if request.building != user.building:
            raise HTTPException(status_code=403, detail="Not authorized to view this request")
        if user.department and request.department != user.department:
            raise HTTPException(status_code=403, detail="Not authorized to view this request")
    elif user.role == Role.EXECUTOR:
        if request.building != user.building:
            raise HTTPException(status_code=403, detail="Not authorized to view this request")
        if user.department and request.department != user.department:
            raise HTTPException(status_code=403, detail="Not authorized to view this request")
    else:
        raise HTTPException(status_code=403, detail="Not authorized to view this request")

    photos = await RequestPhoto.filter(request_id=request_id).order_by('order', 'uploaded_at')

    return [
        PhotoOut(
            id=photo.id,
            file_path=photo.file_path,
            caption=photo.caption,
            order=photo.order,
            uploaded_at=photo.uploaded_at.isoformat()
        )
        for photo in photos
    ]


def generate_thumbnail(file_path: str, max_size: int = 200, quality: int = 60) -> bytes:
    """Generate a thumbnail from an image file"""
    with Image.open(file_path) as img:
        # Apply EXIF orientation to fix rotated images
        try:
            for orientation in ExifTags.TAGS.keys():
                if ExifTags.TAGS[orientation] == 'Orientation':
                    break
            exif = img._getexif()
            if exif is not None:
                orientation_value = exif.get(orientation)
                if orientation_value == 3:
                    img = img.rotate(180, expand=True)
                elif orientation_value == 6:
                    img = img.rotate(270, expand=True)
                elif orientation_value == 8:
                    img = img.rotate(90, expand=True)
        except (AttributeError, KeyError, IndexError, TypeError):
            # No EXIF data or orientation tag
            pass

        # Convert to RGB if necessary (for PNG with transparency)
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')

        # Calculate thumbnail size maintaining aspect ratio
        img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

        # Save to bytes
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=quality, optimize=True)
        buffer.seek(0)
        return buffer.getvalue()


async def check_photo_access(photo: RequestPhoto, user: User):
    """Check if user has access to view the photo"""
    request = photo.request
    if user.role == Role.ADMIN:
        return True
    elif user.role == Role.HEAD:
        if request.building != user.building:
            raise HTTPException(status_code=403, detail="Not authorized to view this photo")
    elif user.role == Role.SPECIALIST:
        if request.building != user.building:
            raise HTTPException(status_code=403, detail="Not authorized to view this photo")
        if user.department and request.department != user.department:
            raise HTTPException(status_code=403, detail="Not authorized to view this photo")
    elif user.role == Role.EXECUTOR:
        if request.building != user.building:
            raise HTTPException(status_code=403, detail="Not authorized to view this photo")
        if user.department and request.department != user.department:
            raise HTTPException(status_code=403, detail="Not authorized to view this photo")
    else:
        raise HTTPException(status_code=403, detail="Not authorized to view this photo")
    return True


@router.get("/photos/{photo_id}/thumbnail")
async def get_photo_thumbnail(
    photo_id: int,
    user: User = Depends(get_current_user),
    size: int = Query(200, ge=50, le=500, description="Max thumbnail size")
):
    """Get a low-resolution thumbnail of the photo"""
    photo = await RequestPhoto.filter(id=photo_id).prefetch_related('request').first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    await check_photo_access(photo, user)

    if not os.path.exists(photo.file_path):
        raise HTTPException(status_code=404, detail="Photo file not found")

    try:
        thumbnail_bytes = generate_thumbnail(photo.file_path, max_size=size)
        return Response(
            content=thumbnail_bytes,
            media_type="image/jpeg",
            headers={"Cache-Control": "public, max-age=86400"}
        )
    except Exception as e:
        # Fallback to original file if thumbnail generation fails
        return FileResponse(photo.file_path)


@router.get("/photos/{photo_id}/file")
async def get_photo_file(photo_id: int, user: User = Depends(get_current_user)):
    photo = await RequestPhoto.filter(id=photo_id).prefetch_related('request').first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    await check_photo_access(photo, user)

    if not os.path.exists(photo.file_path):
        raise HTTPException(status_code=404, detail="Photo file not found")

    return FileResponse(photo.file_path)


@router.delete("/photos/{photo_id}")
async def delete_photo(photo_id: int, user: User = Depends(get_current_user)):
    photo = await RequestPhoto.filter(id=photo_id).prefetch_related('request').first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")


    request = photo.request
    if user.role == Role.ADMIN:
        pass
    elif user.role == Role.HEAD:
        if request.building != user.building:
            raise HTTPException(status_code=403, detail="Not authorized to delete this photo")
    else:
        raise HTTPException(status_code=403, detail="Not authorized to delete photos")


    if os.path.exists(photo.file_path):
        os.remove(photo.file_path)


    await photo.delete()

    return {"detail": "Photo deleted"}


@router.post("/{request_id}/return-to-work")
async def return_postponed_to_work(
    request_id: int,
    user: User = Depends(get_current_user)
) -> RequestOut:
    """Return a postponed request back to 'created' status"""
    request = await Request.get_or_none(id=request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")


    if request.status != RequestStatus.POSTPONED:
        raise HTTPException(status_code=400, detail="Only postponed requests can be returned to work")


    if user.role == Role.ADMIN:
        pass
    elif user.role == Role.HEAD:
        if request.building != user.building:
            raise HTTPException(status_code=403, detail="Not authorized to modify this request")
    else:
        raise HTTPException(status_code=403, detail="Not authorized to return requests to work")


    old_status = request.status
    request.status = RequestStatus.CREATED
    request.closed_at = None
    request.closed_by_id = None
    await request.save()


    await create_history_entry(
        request=request,
        action="status_changed",
        user=user,
        old_status=old_status,
        new_status=RequestStatus.CREATED,
        details=f"{user.first_name} {user.last_name} вернул заявку в работу"
    )


    from routes.notifications import notify_request_returned_to_work
    import asyncio
    asyncio.create_task(notify_request_returned_to_work(request, user))


    request = await Request.filter(id=request_id).prefetch_related('opened_by', 'closed_by', 'photos').first()
    return await request_to_out(request)
