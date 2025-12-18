import os
import json
import asyncio
import logging
import base64
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
import httpx
from pydantic import BaseModel
from auth import get_current_user
from models.tortoise import User, PushSubscription, Request as RequestModel
from models.enums import Building, Role, RequestStatus

# Import pywebpush utilities
from pywebpush import webpush

logger = logging.getLogger(__name__)
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
    logger.info(f"User {user.id} ({user.username}) subscribing to notifications: {subscription.endpoint}")
        
    existing = await PushSubscription.get_or_none(
        user_id=user.id,
        endpoint=subscription.endpoint
    )
    
    if existing:
        logger.info(f"Subscription already exists for user {user.id}, updating keys")
        existing.p256dh = subscription.keys.get("p256dh", "")
        existing.auth = subscription.keys.get("auth", "")
        await existing.save()
        return {"message": "Subscription updated"}
    
    logger.info(f"Creating new subscription for user {user.id}")
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
    logger.info(f"User {user.id} unsubscribing from notifications: {subscription.endpoint}")
    deleted = await PushSubscription.filter(
        user_id=user.id,
        endpoint=subscription.endpoint
    ).delete()
    
    if deleted:
        logger.info(f"Successfully unsubscribed user {user.id}")
        return {"message": "Unsubscribed successfully"}
    
    logger.warning(f"Subscription not found for user {user.id}")
    raise HTTPException(status_code=404, detail="Subscription not found")


async def send_push_notification(
    subscription: PushSubscription,
    payload: NotificationPayload
) -> bool:
    vapid_private_key = os.getenv("VAPID_PRIVATE_KEY")
    vapid_public_key = os.getenv("VAPID_PUBLIC_KEY")
    vapid_email = os.getenv("VAPID_EMAIL", "mailto:admin@example.com")
    
    if not vapid_private_key or not vapid_public_key:
        logger.error("VAPID keys not configured - cannot send push notifications")
        return False
    
    try:
        # Prepare notification data
        notification_data = {
            "title": payload.title,
            "body": payload.body,
            "icon": payload.icon or "/favicon.png",
            "badge": payload.badge or "/favicon.png",
            "data": payload.data or {}
        }
        
        data_json = json.dumps(notification_data)
        
        logger.debug(f"Sending push notification to {subscription.endpoint}: {payload.title}")
        
        # Prepare subscription info
        subscription_info = {
            "endpoint": subscription.endpoint,
            "keys": {
                "p256dh": subscription.p256dh,
                "auth": subscription.auth
            }
        }
        
        # Use webpush in async context with thread executor
        def _send_webpush():
            return webpush(
                subscription_info=subscription_info,
                data=data_json,
                vapid_private_key=vapid_private_key,
                vapid_claims={"sub": vapid_email},
                timeout=10
            )
        
        # Run in thread pool to avoid blocking
        response = await asyncio.to_thread(_send_webpush)
        
        logger.info(f"✓ Push notification sent successfully to {subscription.endpoint}")
        return True
                
    except Exception as e:
        error_str = str(e).lower()
        
        # Check for 404/410 errors (invalid subscriptions)
        if "404" in error_str or "410" in error_str or "push subscription has expired" in error_str:
            try:
                await subscription.delete()
                logger.warning(f"Deleted invalid subscription: {subscription.endpoint}")
            except Exception as delete_error:
                logger.error(f"Failed to delete subscription {subscription.endpoint}: {delete_error}")
            return False
        
        logger.exception(f"✗ Error sending push notification to {subscription.endpoint}: {e}")
        return False


async def notify_department_employees(
    department: str,
    building: Building,
    payload: NotificationPayload
):
    logger.info(f"Notifying department {department} in building {building}")
        
    users = await User.filter(
        building=building,
        department=department
    )
    
    logger.info(f"Found {len(users)} users in department {department}")
    await send_to_users(users, payload)


async def send_to_users(users: List[User], payload: NotificationPayload):
    logger.info(f"Starting notification to {len(users)} users: '{payload.title}'")
    
    tasks = []
    subscription_count = 0
    user_with_subs = 0
    user_without_subs = 0
    
    for user in users:
        subscriptions = await PushSubscription.filter(user_id=user.id)
        subscription_count += len(subscriptions)
        
        if len(subscriptions) > 0:
            user_with_subs += 1
            logger.debug(f"  - User {user.id} ({user.username}): {len(subscriptions)} subscriptions")
        else:
            user_without_subs += 1
            logger.debug(f"  - User {user.id} ({user.username}): NO subscriptions")
        
        for subscription in subscriptions:
            tasks.append(send_push_notification(subscription, payload))
    
    logger.info(f"Summary: {user_with_subs} users with subscriptions, {user_without_subs} users without. Total {subscription_count} subscriptions to notify")
    
    if tasks:
        results = await asyncio.gather(*tasks, return_exceptions=True)
        successful = sum(1 for r in results if r is True)
        failed = sum(1 for r in results if r is not True)
        logger.info(f"Notification results: {successful}/{len(results)} sent successfully, {failed} failed")
    else:
        logger.warning("⚠ No subscriptions found to notify")


async def notify_request_created(request: RequestModel, creator: User):
    try:
        logger.info(f"→ notify_request_created: request_id={request.id}, creator_id={creator.id}")

        target_users = []
        
        # Get all admins
        admins = await User.filter(role=Role.ADMIN)
        target_users.extend(admins)
        logger.debug(f"  Added {len(admins)} admins")
        
        # Get heads for this building
        heads = await User.filter(role=Role.HEAD, building=request.building)
        target_users.extend(heads)
        logger.debug(f"  Added {len(heads)} heads for building {request.building}")
        
        # Get specialists and executors for this department
        if request.department:
            specialists_and_executors = await User.filter(
                building=request.building,
                role__in=[Role.SPECIALIST, Role.EXECUTOR],
                department=request.department
            )
            target_users.extend(specialists_and_executors)
            logger.debug(f"  Added {len(specialists_and_executors)} specialists/executors for department {request.department}")
        
        # Remove creator from target list
        target_users = [u for u in target_users if u.id != creator.id]
        
        # Remove duplicates
        target_users = list({u.id: u for u in target_users}.values())
        logger.info(f"  Total target users: {len(target_users)}")
        
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
        else:
            logger.warning(f"⚠ No target users found for request created notification")
    except Exception as e:
        logger.exception(f"✗ ERROR in notify_request_created: {e}")


async def notify_status_change_requested(request: RequestModel, executor: User):
    try:
        logger.info(f"→ notify_status_change_requested: request_id={request.id}, executor_id={executor.id}")

        target_users = []
        
        # Get all admins
        admins = await User.filter(role=Role.ADMIN)
        target_users.extend(admins)
        logger.debug(f"  Added {len(admins)} admins")
        
        # Get heads for this building
        heads = await User.filter(role=Role.HEAD, building=request.building)
        target_users.extend(heads)
        logger.debug(f"  Added {len(heads)} heads for building {request.building}")
        
        # Remove duplicates
        target_users = list({u.id: u for u in target_users}.values())
        logger.info(f"  Total target users: {len(target_users)}")
        
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
        else:
            logger.warning(f"⚠ No target users found for status change requested notification")
    except Exception as e:
        logger.exception(f"✗ ERROR in notify_status_change_requested: {e}")


async def notify_status_change_approved(request: RequestModel, approved_status: RequestStatus):
    try:
        logger.info(f"→ notify_status_change_approved: request_id={request.id}, new_status={approved_status}")

        target_users = []
        payload = None
        
        if approved_status == RequestStatus.COMPLETED:
            logger.debug(f"  Status is COMPLETED - notifying admins, heads, and department staff")
            
            # Get all admins
            admins = await User.filter(role=Role.ADMIN)
            target_users.extend(admins)
            logger.debug(f"    Added {len(admins)} admins")
            
            # Get heads
            heads = await User.filter(role=Role.HEAD, building=request.building)
            target_users.extend(heads)
            logger.debug(f"    Added {len(heads)} heads")
            
            # Get specialists and executors
            if request.department:
                specialists_and_executors = await User.filter(
                    building=request.building,
                    role__in=[Role.SPECIALIST, Role.EXECUTOR],
                    department=request.department
                )
                target_users.extend(specialists_and_executors)
                logger.debug(f"    Added {len(specialists_and_executors)} specialists/executors")
            
            # Remove duplicates
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
            logger.debug(f"  Status is POSTPONED - notifying admins only")
            
            # Get all admins
            admins = await User.filter(role=Role.ADMIN)
            target_users.extend(admins)
            logger.debug(f"    Added {len(admins)} admins")
            
            payload = NotificationPayload(
                title=f"Заявка отложена: {request.title}",
                body=f"Статус изменен на 'Отложено'",
                data={
                    "url": f"/requests/{request.id}",
                    "requestId": request.id,
                    "action": "status_postponed"
                }
            )
        else:
            logger.warning(f"⚠ Unknown status: {approved_status}")
        
        if target_users and payload:
            logger.info(f"  Total target users: {len(target_users)}")
            await send_to_users(target_users, payload)
        else:
            logger.warning(f"⚠ No target users or payload for status change approved notification")
    except Exception as e:
        logger.exception(f"✗ ERROR in notify_status_change_approved: {e}")


async def notify_status_change_rejected(
    request: RequestModel,
    requester: User,
    rejection_reason: Optional[str] = None
):
    try:
        logger.info(f"→ notify_status_change_rejected: request_id={request.id}, requester_id={requester.id}, reason='{rejection_reason}'")

        target_users = []
        
        # Notify the requester
        target_users.append(requester)
        logger.debug(f"  Added requester: {requester.id}")
        
        # Notify all admins
        admins = await User.filter(role=Role.ADMIN)
        target_users.extend(admins)
        logger.debug(f"  Added {len(admins)} admins")
        
        # Remove duplicates
        target_users = list({u.id: u for u in target_users}.values())
        logger.info(f"  Total target users: {len(target_users)}")
        
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
    except Exception as e:
        logger.exception(f"✗ ERROR in notify_status_change_rejected: {e}")


async def notify_request_returned_to_work(request: RequestModel, user: User):
    try:
        logger.info(f"→ notify_request_returned_to_work: request_id={request.id}, user_id={user.id}")

        target_users = []
        
        # Get all admins
        admins = await User.filter(role=Role.ADMIN)
        target_users.extend(admins)
        logger.debug(f"  Added {len(admins)} admins")
        
        # Get heads for this building
        heads = await User.filter(role=Role.HEAD, building=request.building)
        target_users.extend(heads)
        logger.debug(f"  Added {len(heads)} heads")
        
        # Get specialists and executors for this department
        if request.department:
            specialists_and_executors = await User.filter(
                building=request.building,
                role__in=[Role.SPECIALIST, Role.EXECUTOR],
                department=request.department
            )
            target_users.extend(specialists_and_executors)
            logger.debug(f"  Added {len(specialists_and_executors)} specialists/executors")
        
        # Remove the user who returned the request
        target_users = [u for u in target_users if u.id != user.id]
        
        # Remove duplicates
        target_users = list({u.id: u for u in target_users}.values())
        logger.info(f"  Total target users: {len(target_users)}")
        
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
        else:
            logger.warning(f"⚠ No target users found for request returned to work notification")
    except Exception as e:
        logger.exception(f"✗ ERROR in notify_request_returned_to_work: {e}")
