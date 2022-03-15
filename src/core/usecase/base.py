from src.core.exceptions.base import NotFoundError


class SuccessResultBase:
    ...


class FailResultBase:
    ...


class UseCaseBase:
    ...

    def get_user_by_identification(self, identification):
        if not hasattr(self, 'user_repo'):
            raise TypeError(f"UseCase {self} hasn't attr user_repo")
        if isinstance(identification, int):
            pass
        if isinstance(identification, str):
            pass
        raise NotFoundError(obj="User", search_spec=str(identification))