from pydantic import BaseModel, EmailStr, Field, field_validator


class StudentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("Name must be a string")

        name = value.strip()

        if not name:
            raise ValueError("Name cannot be empty")

        return name


class StudentResponse(BaseModel):
    id: int
    name: str
    email: EmailStr