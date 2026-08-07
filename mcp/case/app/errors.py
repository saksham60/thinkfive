class CaseMcpError(Exception):
    def __init__(self, code: str, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.code, self.safe_message, self.retryable = code, message, retryable


def fail(code: str, message: str) -> CaseMcpError:
    return CaseMcpError(code, message)
