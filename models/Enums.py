from enum import Enum


class MaterialType(str, Enum):
    video = "video"
    document = "document"
    presentation = "presentation"
    text = "text"


class QuestionType(str, Enum):
    single = "single"
    multiple = "multiple"
    text = "text"


class RoleType(str, Enum):
    student = "student"
    teacher = "teacher"
    admin = "admin"


class ApplicationStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
