from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from tortoise.expressions import Q

from auth import get_current_user
from models.enums import Building, Department, RequestStatus, Role
from models.tortoise import Request, User
from models.pydantic import StatsOut

router = APIRouter()


@router.get("/")
async def get_stats(
    building: Optional[Building] = Query(None),
    department: Optional[Department] = Query(None),
    period: str = Query("month", regex="^(day|week|month)$"),
    user: User = Depends(get_current_user)
) -> StatsOut:
    """
    Get statistics for requests with optional filters:
    - building: filter by building
    - department: filter by department (IT or АХЧ)
    - period: time period (day, week, month)
    
    For head of department: automatically filters by their building and department
    """
    
    
    if user.role == Role.HEAD:
        if not user.building or not user.department:
            raise HTTPException(status_code=400, detail="У руководителя отделения должны быть указаны корпус и отдел")
        building = user.building
        department = Department(user.department)
    
    
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
        total_time = sum(
            (req.closed_at - req.opened_at).total_seconds() / 3600  
            for req in closed_reqs
        )
        avg_processing_time = total_time / len(closed_reqs)
    else:
        avg_processing_time = 0.0
    
    return StatsOut(
        total_requests=total_requests,
        open_requests=open_requests,
        closed_requests=closed_requests,
        ratio=ratio,
        avg_processing_time_hours=avg_processing_time
    )
