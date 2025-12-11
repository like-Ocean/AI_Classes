from enum import Enum


class CourseRoleFilter(str, Enum):
    all = "all"
    created = "created"
    editor = "editor"
