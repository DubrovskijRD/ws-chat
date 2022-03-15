from typing import Union
from dataclasses import dataclass

from src.core.usecase.base import SuccessResultBase, FailResultBase, UseCaseBase


@dataclass
class SuccessResult(SuccessResultBase):
    device_name: str


@dataclass
class FailResult(FailResultBase):
    code: int
    msg: str

class UseCase(UseCaseBase):
    SuccessResult = SuccessResult
    FailResult = FailResult

    def __init__(self):
        ...

    def execute(self, ) -> Union[SuccessResult, FailResult]:
        ...
