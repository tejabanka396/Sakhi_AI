from abc import ABC, abstractmethod
from typing import List, Tuple

class SMSProvider(ABC):
    @abstractmethod
    async def send_otp(self, phone: str, otp: str) -> Tuple[bool, str]:
        """
        Sends an OTP code to the recipient phone number.
        Returns: (success: bool, status_message_or_error: str)
        """
        pass

    @abstractmethod
    def validate_configuration(self) -> List[str]:
        """
        Returns list of missing configuration environment variables if any.
        """
        pass
