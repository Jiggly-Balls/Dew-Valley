from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from game_state import State


class BaseError(Exception):
    """The base class to all custom errors."""

    def __init__(
        self, *args, last_state: Optional[State] = None, **kwargs
    ) -> None:
        super().__init__(*args)

        self.last_state = last_state
        for key, value in kwargs.items():
            setattr(self, key, value)


class StateError(BaseError):
    """Raised when an operation is done over an invalid state."""

    def __init__(
        self, *args, last_state: Optional[State] = None, **kwargs
    ) -> None:
        super().__init__(*args, last_state=last_state, **kwargs)


class StateLoadError(BaseError):
    """Raised when an error occurs in loading / unloading a state."""

    def __init__(
        self, *args, last_state: Optional[State] = None, **kwargs
    ) -> None:
        super().__init__(*args, last_state=last_state, **kwargs)


class ExitStateError(BaseError):
    """An error class used to exit the current state."""

    def __init__(
        self, *args, last_state: Optional[State] = None, **kwargs
    ) -> None:
        super().__init__(*args, last_state=last_state, **kwargs)


class ExitGameError(BaseError):
    """An error class used to exit out of the game"""

    def __init__(
        self, *args, last_state: Optional[State] = None, **kwargs
    ) -> None:
        super().__init__(*args, last_state=last_state, **kwargs)
