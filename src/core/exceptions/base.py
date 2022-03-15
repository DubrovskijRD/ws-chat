class DomainError(Exception):
    """ base domain error """
    code: int

    def to_dict(self):
        return {
            "status": "fail",
            "error": {"message": str(self), "code": self.code}
        }


class ValidationError(DomainError):
    code = 1

    def __init__(self, msg=None, obj=None, value=None):
        self.obj = obj
        self.value = value
        super().__init__(msg or f"Not valid {obj}: {value}")


class UnauthorizedError(DomainError):
    code = 2

    def __init__(self):
        super().__init__("Unauthorized")


class ForbiddenError(DomainError):
    code = 3

    def __init__(self, msg=None):
        msg = msg or "Forbidden"
        super().__init__(msg)


class NotFoundError(DomainError):
    code = 4

    def __init__(self, msg=None, obj=None, search_spec=None):
        self.obj = obj
        self.search_spec = search_spec
        super().__init__(msg or self.error_msg(obj, search_spec))

    @staticmethod
    def error_msg(obj, spec):
        return f"Not found {obj}: {spec}"


class NotUniqueError(DomainError):
    code = 5

    def __init__(self, msg=None, obj=None, value=None):
        self.obj = obj
        self.value = value
        super().__init__(msg or f"Not unique {obj}: {value}")


class StorageError(DomainError):
    pass