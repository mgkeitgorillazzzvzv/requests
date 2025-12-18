from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from tortoise.expressions import Q

from auth import get_current_user
from models.enums import Building, Department, RequestStatus, Role
from models.tortoise import Request, RequestStatusChangeRequest, User
from models.pydantic import StatsOut

router = APIRouter()


@router.get("/")
async def get_stats(
    building: Optional[Building] = Query(None),
    department: Optional[Department] = Query(None),
    period: str = Query("month", regex="^(day|week|month)$"),
    user: User = Depends(get_current_user)
) -> StatsOut:
    







    
    
    if user.role == Role.HEAD:
        if not user.building:
            raise HTTPException(status_code=400, detail="У руководителя отделения должен быть указан корпус")
        building = user.building
        
    
    now = datetime.utcnow()
    if period == "day":
        start_date = now - timedelta(days=1)
    elif period == "week":
        start_date = now - timedelta(weeks=1)
    else:  
        start_date = now - timedelta(days=30)
    
    
    filters = Q(opened_at__gte=start_date)
    
    if building:
        filters &= Q(building=building)
    
    if department:
        filters &= Q(department=department.value)
    
    
    total_requests = await Request.filter(filters).count()
    
    
    open_requests = await Request.filter(
        filters, 
        status__in=[RequestStatus.CREATED, RequestStatus.PENDING_APPROVAL]
    ).count()
    
    
    closed_requests = await Request.filter(
        filters, 
        status__in=[RequestStatus.COMPLETED, RequestStatus.POSTPONED]
    ).count()
    
    
    ratio = closed_requests / total_requests if total_requests > 0 else 0.0
    
    
    closed_reqs = await Request.filter(
        filters, 
        status__in=[RequestStatus.COMPLETED, RequestStatus.POSTPONED], 
        closed_at__isnull=False
    ).all()
    
    if closed_reqs:
        execution_times = []
        for req in closed_reqs:
            last_approved = await RequestStatusChangeRequest.filter(
                request=req,
                approved=True,
                requested_status__in=[RequestStatus.COMPLETED, RequestStatus.POSTPONED]
            ).order_by('-reviewed_at').first()
            
            if last_approved and last_approved.created_at:
                time_diff = (last_approved.created_at - req.opened_at).total_seconds() / 3600
                execution_times.append(time_diff)
        
        execution_time = sum(execution_times) / len(execution_times) if execution_times else 0.0
    else:
        execution_time = 0.0
    
    review_times = []
    for req in closed_reqs:
        last_change_request = await RequestStatusChangeRequest.filter(
            request=req,
            approved=True,
            requested_status__in=[RequestStatus.COMPLETED, RequestStatus.POSTPONED]
        ).order_by('-reviewed_at').first()
        
        if last_change_request and last_change_request.reviewed_at:
            review_time = (last_change_request.reviewed_at - last_change_request.created_at).total_seconds() / 3600
            review_times.append(review_time)
    
    avg_review_time = sum(review_times) / len(review_times) if review_times else 0.0
    
    return StatsOut(
        total_requests=total_requests,
        open_requests=open_requests,
        closed_requests=closed_requests,
        ratio=ratio,
        execution_time_hours=execution_time,
        avg_review_time_hours=avg_review_time
    )
