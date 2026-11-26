from fastapi import HTTPException


def not_found(message: str = "Record not found") -> HTTPException:
    return HTTPException(status_code=404, detail=message)

