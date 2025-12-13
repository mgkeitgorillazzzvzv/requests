from enum import Enum


class Role(str, Enum):
	ADMIN = "администратор"
	HEAD = "заведующий отделением"
	SPECIALIST = "специалист"
	EXECUTOR = "исполнитель"

class Department(str, Enum):
    IT = "IT"
    MAINTENANCE = "АХЧ"

class Building(str, Enum):
	MILLIONSHCHIKOVA = "Центр программирования и кибербезопасности"
	KOLOMENSKAYA = "Дизайн колледж"
	SUDOSTROITELNAYA = "Центр городских технологий"
	KHARKOVSKY = "IT.Бирюлево"


class RequestStatus(str, Enum):
	CREATED = "создано"
	PENDING_APPROVAL = "ожидает подтверждения"
	COMPLETED = "выполнено"
	POSTPONED = "отложено"
	PENDING_CREATION_APPROVAL = "ожидает создания"
