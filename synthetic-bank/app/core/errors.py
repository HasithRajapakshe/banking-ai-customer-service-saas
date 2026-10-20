from dataclasses import dataclass


@dataclass
class AppError(Exception):
    status_code: int
    code: str
    message: str