"""Customer domain value objects."""

from dataclasses import dataclass


@dataclass(frozen=True)
class EmailAddress:
    """Email address value object."""

    value: str

    def __post_init__(self) -> None:
        if not self.value or "@" not in self.value:
            raise ValueError("Invalid email address")


@dataclass(frozen=True)
class PhoneNumber:
    """Phone number value object."""

    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("Phone number cannot be empty")
