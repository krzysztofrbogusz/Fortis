from dataclasses import dataclass
from typing import NoReturn, TypeVar

T = TypeVar("T")
E = TypeVar("E")


@dataclass(frozen=True)
class Ok[T]:
    """Represents a successful outcome.

    Args:
        value: The success value.
    """

    value: T

    def is_ok(self) -> bool:
        """Checks if the result is Ok.

        Returns:
            True, since this is an Ok instance.
        """
        return True

    def is_err(self) -> bool:
        """Checks if the result is Err.

        Returns:
            False, since this is an Ok instance.
        """
        return False

    def unwrap(self) -> T:
        """Extracts the successful value.

        Returns:
            The inner value.
        """
        return self.value

    def unwrap_err(self) -> NoReturn:
        """Attempts to extract the error, but fails because this is Ok.

        Raises:
            ValueError: Always raised to prevent accessing a non-existent error.
        """
        raise ValueError(f"Called unwrap_err() on an Ok value: {self.value}")

    def unwrap_or(self, default: T) -> T:  # noqa: ARG002
        """Returns the contained value, ignoring the default.

        Args:
            default: The fallback value (unused here).

        Returns:
            The inner success value.
        """
        return self.value


@dataclass(frozen=True)
class Err[E]:
    """Represents a failed outcome.

    Args:
        error: The error value or message.
    """

    error: E

    def is_ok(self) -> bool:
        """Checks if the result is Ok.

        Returns:
            False, since this is an Err instance.
        """
        return False

    def is_err(self) -> bool:
        """Checks if the result is Err.

        Returns:
            True, since this is an Err instance.
        """
        return True

    def unwrap(self) -> NoReturn:
        """Attempts to extract the value, but fails because this is an error.

        Raises:
            ValueError: Always raised to prevent accessing a non-existent value.
        """
        raise ValueError(f"Called unwrap() on an Err value: {self.error}")

    def unwrap_err(self) -> E:
        """Extracts the error value.

        Returns:
            The inner error message or object.
        """
        return self.error

    def unwrap_or(self, default: T) -> T:
        """Returns the provided default value since this is an error.

        Args:
            default: The fallback value to return.

        Returns:
            The fallback value.
        """
        return default


# The TypeAlias tying it all together
type Result[T, E] = Ok[T] | Err[E]
