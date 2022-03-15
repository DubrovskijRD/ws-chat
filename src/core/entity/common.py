from dataclasses import dataclass
from email_validator import validate_email, EmailNotValidError

from src.core.exceptions.base import ValidationError


@dataclass(frozen=True, init=False)
class Email:
    value: str

    def __init__(self, value: str):
        try:
            valid = validate_email(value)
            self.__setattr__('value', valid.email)
        except EmailNotValidError as e:
            # email is not valid, exception message is human-readable
            raise ValidationError(str(e), obj="email", value=value)
