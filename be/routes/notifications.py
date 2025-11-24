import os
import json
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pywebpush import webpush, WebPushException
from pydantic import BaseModel
from auth import get_current_user
from models.tortoise import User, PushSubscription, Request as RequestModel
from models.enums import Building, get_department_by_role, Role, RequestStatus

router = APIRouter()


class SubscribeRequest(BaseModel):
    endpoint: str
    keys: dict  


class NotificationPayload(BaseModel):
    title: str
    body: str
    icon: Optional[str] = None
    badge: Optional[str] = None
    data: Optional[dict] = None


@router.post("/subscribe")
async def subscribe_to_notifications(
    subscription: SubscribeRequest,
    user: User = Depends(get_current_user)
):
    """Subscribe user to push notifications"""
    
    existing = await PushSubscription.get_or_none(
        user_id=user.id,
        endpoint=subscription.endpoint
    )
    
    if existing:
        
        existing.p256dh = subscription.keys.get("p256dh", "")
        existing.auth = subscription.keys.get("auth", "")
        await existing.save()
        return {"message": "Subscription updated"}
    
    
    await PushSubscription.create(
        user_id=user.id,
        endpoint=subscription.endpoint,
        p256dh=subscription.keys.get("p256dh", ""),
        auth=subscription.keys.get("auth", "")
    )
    
    return {"message": "Subscribed successfully"}


@router.post("/unsubscribe")
async def unsubscribe_from_notifications(
    subscription: SubscribeRequest,
    user: User = Depends(get_current_user)
):
    """Unsubscribe user from push notifications"""
    deleted = await PushSubscription.filter(
        user_id=user.id,
        endpoint=subscription.endpoint
    ).delete()
    
    if deleted:
        return {"message": "Unsubscribed successfully"}
    
    raise HTTPException(status_code=404, detail="Subscription not found")


async def send_push_notification(
    subscription: PushSubscription,
    payload: NotificationPayload
) -> bool:
    """Send push notification to a specific subscription"""
    vapid_private_key = os.getenv("VAPID_PRIVATE_KEY")
    vapid_public_key = os.getenv("VAPID_PUBLIC_KEY")
    vapid_email = os.getenv("VAPID_EMAIL", "mailto:admin@example.com")
    
    if not vapid_private_key or not vapid_public_key:
        print("VAPID keys not configured")
        return False
    
    subscription_info = {
        "endpoint": subscription.endpoint,
        "keys": {
            "p256dh": subscription.p256dh,
            "auth": subscription.auth
        }
    }
    
    notification_data = {
        "title": payload.title,
        "body": payload.body,
        "icon": payload.icon or "/favicon.png",
        "badge": payload.badge or "/favicon.png",
        "data": payload.data or {}
    }
    
    try:
        webpush(
            subscription_info=subscription_info,
            data=json.dumps(notification_data),
            vapid_private_key=vapid_private_key,
            vapid_claims={
                "sub": vapid_email
            }
        )
        return True
    except WebPushException as e:
        print(f"WebPush failed: {e}")
        
        if e.response and e.response.status_code in [404, 410]:
            await subscription.delete()
        return False


async def notify_department_employees(
    department: str,
    building: Building,
    payload: NotificationPayload
):
    """Send notification to all employees of a department in a specific building"""
    
    users = await User.filter(
        building=building,
        department=department
    )
    
    
    for user in users:
        subscriptions = await PushSubscription.filter(user_id=user.id)
        for subscription in subscriptions:
            print(f"Sending notification to {subscription.endpoint}")
            await send_push_notification(subscription, payload)


async def send_to_users(users: List[User], payload: NotificationPayload):
    """Send notification to a list of users"""
    for user in users:
        subscriptions = await PushSubscription.filter(user_id=user.id)
        for subscription in subscriptions:
            await send_push_notification(subscription, payload)


async def notify_request_created(request: RequestModel, creator: User):
    """
    Уведомление о создании заявки отправляется всем, кто может просмотреть её:
    - Администратор (все заявки)
    - Заведующий (заявки на своей площадке)
    - Специалисты и исполнители (заявки своего отдела на своей площадке)
    """
    target_users = []
    
    
    admins = await User.filter(role=Role.ADMIN)
    target_users.extend(admins)
    
    
    heads = await User.filter(role=Role.HEAD, building=request.building)
    target_users.extend(heads)
    
    
    if request.department:
        specialists_and_executors = await User.filter(
            building=request.building,
            role__in=[Role.SPECIALIST, Role.EXECUTOR],
            department=request.department
        )
        target_users.extend(specialists_and_executors)
    
    
    target_users = [u for u in target_users if u.id != creator.id]
    
    
    target_users = list({u.id: u for u in target_users}.values())
    
    if target_users:
        payload = NotificationPayload(
            title=f"Новая заявка",
            body=f"{request.title}",
            data={
                "url": f"/requests/{request.id}",
                "requestId": request.id,
                "action": "request_created"
            }
        )
        await send_to_users(target_users, payload)


async def notify_status_change_requested(request: RequestModel, executor: User):
    """
    Уведомление о том, что заявка ожидает подтверждения (pending approval)
    Отправляется только администраторам и руководителям площадки
    """
    target_users = []
    
    
    admins = await User.filter(role=Role.ADMIN)
    target_users.extend(admins)
    
    
    heads = await User.filter(role=Role.HEAD, building=request.building)
    target_users.extend(heads)
    
    
    target_users = list({u.id: u for u in target_users}.values())
    
    if target_users:
        payload = NotificationPayload(
            title=f"Заявка ожидает подтверждения: {request.title}",
            body=f"Исполнитель {executor.first_name} {executor.last_name} отправил на подтверждение",
            data={
                "url": f"/requests/{request.id}",
                "requestId": request.id,
                "action": "status_change_requested"
            }
        )
        await send_to_users(target_users, payload)


async def notify_status_change_approved(request: RequestModel, approved_status: RequestStatus):
    """
    Уведомление об изменении статуса при подтверждении:
    - "выполнено" -> всем, кто может просмотреть
    - "отложено" -> админу
    """
    target_users = []
    
    if approved_status == RequestStatus.COMPLETED:
        
        admins = await User.filter(role=Role.ADMIN)
        target_users.extend(admins)
        
        heads = await User.filter(role=Role.HEAD, building=request.building)
        target_users.extend(heads)
        
        if request.department:
            specialists_and_executors = await User.filter(
                building=request.building,
                role__in=[Role.SPECIALIST, Role.EXECUTOR],
                department=request.department
            )
            target_users.extend(specialists_and_executors)
        
        
        target_users = list({u.id: u for u in target_users}.values())
        
        payload = NotificationPayload(
            title=f"Заявка выполнена: {request.title}",
            body=f"Статус изменен на 'Выполнено'",
            data={
                "url": f"/requests/{request.id}",
                "requestId": request.id,
                "action": "status_completed"
            }
        )
    
    elif approved_status == RequestStatus.POSTPONED:
        
        admins = await User.filter(role=Role.ADMIN)
        target_users.extend(admins)
        
        payload = NotificationPayload(
            title=f"Заявка отложена: {request.title}",
            body=f"Статус изменен на 'Отложено'",
            data={
                "url": f"/requests/{request.id}",
                "requestId": request.id,
                "action": "status_postponed"
            }
        )
    
    if target_users:
        await send_to_users(target_users, payload)


async def notify_status_change_rejected(
    request: RequestModel,
    requester: User,
    rejection_reason: Optional[str] = None
):
    """
    Уведомление при отклонении запроса на изменение статуса:
    Отправляется автору запроса и админам
    """
    target_users = []
    
    
    target_users.append(requester)
    
    
    admins = await User.filter(role=Role.ADMIN)
    target_users.extend(admins)
    
    
    target_users = list({u.id: u for u in target_users}.values())
    
    reason_text = f": {rejection_reason}" if rejection_reason else ""
    payload = NotificationPayload(
        title=f"Запрос отклонен: {request.title}",
        body=f"Заявка вернулась в статус 'Создано'{reason_text}",
        data={
            "url": f"/requests/{request.id}",
            "requestId": request.id,
            "action": "status_change_rejected"
        }
    )
    
    await send_to_users(target_users, payload)


async def notify_request_returned_to_work(request: RequestModel, user: User):
    """
    Уведомление о возврате отложенной заявки в работу.
    Отправляется всем, кто может просмотреть заявку (кроме того, кто вернул)
    """
    target_users = []
    
    
    admins = await User.filter(role=Role.ADMIN)
    target_users.extend(admins)
    
    
    heads = await User.filter(role=Role.HEAD, building=request.building)
    target_users.extend(heads)
    
    
    if request.department:
        specialists_and_executors = await User.filter(
            building=request.building,
            role__in=[Role.SPECIALIST, Role.EXECUTOR],
            department=request.department
        )
        target_users.extend(specialists_and_executors)
    
    
    target_users = [u for u in target_users if u.id != user.id]
    
    
    target_users = list({u.id: u for u in target_users}.values())
    
    if target_users:
        payload = NotificationPayload(
            title=f"Заявка возвращена в работу: {request.title}",
            body=f"Пользователь {user.first_name} {user.last_name} вернул заявку в работу",
            data={
                "url": f"/requests/{request.id}",
                "requestId": request.id,
                "action": "request_returned_to_work"
            }
        )
        await send_to_users(target_users, payload)
