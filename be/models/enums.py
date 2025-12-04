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
	MILLIONSHCHIKOVA = "Миллионщикова"
	KOLOMENSKAYA = "Коломенская"
	SUDOSTROITELNAYA = "Судостроительная"
	KHARKOVSKY = "Харьковский"


class RequestStatus(str, Enum):
	CREATED = "создано"
	PENDING_APPROVAL = "ожидает подтверждения"
	COMPLETED = "выполнено"
	POSTPONED = "отложено"

