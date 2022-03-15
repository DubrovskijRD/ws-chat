from enum import Enum


class RoomMessageType(Enum):
    DEFAULT = 1

    def __str__(self):
        return str(self.value)