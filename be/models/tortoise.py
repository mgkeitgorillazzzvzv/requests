

from tortoise import fields, models

from models.enums import Building, Role, RequestStatus


class User(models.Model):
	id = fields.IntField(pk=True)
	first_name = fields.CharField(max_length=255)
	last_name = fields.CharField(max_length=255)
	username = fields.CharField(max_length=150, unique=True, index=True)
	password = fields.CharField(max_length=255)
	role = fields.CharEnumField(Role, max_length=50)
	building = fields.CharEnumField(Building, max_length=50, null=True)
	department = fields.CharField(max_length=50, null=True)
	created_at = fields.DatetimeField(auto_now_add=True)

	class Meta:
		table = "users"

	def __str__(self) -> str:
		return f"{self.first_name} {self.last_name}<{self.username}>"


class Request(models.Model):
	id = fields.IntField(pk=True)
	status = fields.CharEnumField(RequestStatus, max_length=50, default=RequestStatus.CREATED)
	title = fields.CharField(max_length=255)
	description = fields.TextField(null=True)
	building = fields.CharEnumField(Building, max_length=50)
	opened_by = fields.ForeignKeyField("models.User", related_name="requests_opened", on_delete=fields.CASCADE, null=True)
	closed_by = fields.ForeignKeyField(
		"models.User", related_name="requests_closed", null=True, on_delete=fields.SET_NULL
	)
	opened_at = fields.DatetimeField(auto_now_add=True)
	closed_at = fields.DatetimeField(null=True)
	department = fields.CharField(max_length=255, null=True)
	urgent = fields.BooleanField(default=False)
	is_anonymous = fields.BooleanField(default=False)

	class Meta:
		table = "requests"

	def __str__(self) -> str: 
		return f"Request {self.id} ({self.status.value})"


class RequestPhoto(models.Model):
	id = fields.IntField(pk=True)
	request = fields.ForeignKeyField("models.Request", related_name="photos", on_delete=fields.CASCADE)
	file_path = fields.CharField(max_length=1024)
	caption = fields.CharField(max_length=255, null=True)
	order = fields.IntField(default=0)
	uploaded_at = fields.DatetimeField(auto_now_add=True)

	class Meta:
		table = "request_photos"

	def __str__(self) -> str:
		return f"Photo {self.id} for Request {self.request_id}"


class PushSubscription(models.Model):
	id = fields.IntField(pk=True)
	user = fields.ForeignKeyField("models.User", related_name="push_subscriptions", on_delete=fields.CASCADE)
	endpoint = fields.CharField(max_length=1024)
	p256dh = fields.CharField(max_length=512)
	auth = fields.CharField(max_length=512)
	created_at = fields.DatetimeField(auto_now_add=True)

	class Meta:
		table = "push_subscriptions"
		unique_together = (("user", "endpoint"),)

	def __str__(self) -> str:
		return f"PushSubscription {self.id} for User {self.user_id}"


class RequestStatusChangeRequest(models.Model):
	"""Запрос на изменение статуса заявки (от исполнителя к заведующему)"""
	id = fields.IntField(pk=True)
	request = fields.ForeignKeyField("models.Request", related_name="status_change_requests", on_delete=fields.CASCADE)
	requested_by = fields.ForeignKeyField("models.User", related_name="status_changes_requested", on_delete=fields.CASCADE)
	requested_status = fields.CharEnumField(RequestStatus, max_length=50)  
	reason = fields.TextField(null=True)  
	photo = fields.ForeignKeyField("models.RequestPhoto", related_name="status_change_requests", null=True, on_delete=fields.SET_NULL)  
	created_at = fields.DatetimeField(auto_now_add=True)
	reviewed_at = fields.DatetimeField(null=True)
	reviewed_by = fields.ForeignKeyField("models.User", related_name="status_changes_reviewed", null=True, on_delete=fields.SET_NULL)
	approved = fields.BooleanField(null=True)  
	rejection_reason = fields.TextField(null=True)
	rejection_photo = fields.ForeignKeyField("models.RequestPhoto", related_name="rejection_photos", null=True, on_delete=fields.SET_NULL)

	class Meta:
		table = "request_status_change_requests"

	def __str__(self) -> str:
		return f"StatusChangeRequest {self.id} for Request {self.request_id}"


class RequestHistory(models.Model):
	"""История изменений заявки"""
	id = fields.IntField(pk=True)
	request = fields.ForeignKeyField("models.Request", related_name="history", on_delete=fields.CASCADE)
	action = fields.CharField(max_length=255)  
	performed_by = fields.ForeignKeyField("models.User", related_name="actions_performed", on_delete=fields.CASCADE)
	old_status = fields.CharEnumField(RequestStatus, max_length=50, null=True)
	new_status = fields.CharEnumField(RequestStatus, max_length=50, null=True)
	details = fields.TextField(null=True)  
	created_at = fields.DatetimeField(auto_now_add=True)

	class Meta:
		table = "request_history"
		ordering = ["-created_at"]

	def __str__(self) -> str:
		return f"History {self.id} for Request {self.request_id}: {self.action}"

