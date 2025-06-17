from typing import Type, Any, Union, List
from datetime import date, datetime

class Field(object):
    def __init__(
            self,
            required: bool = False,
            nullable: bool = False,
            field_type: Type[Any] = str
    ):
        self.required = required
        self.nullable = nullable
        self.field_type = field_type
        self.field_name = None


    def validate(self, value: Any) -> Any:
        if value is None:
            if not self.nullable:
                raise ValueError(f"{self.field_name} cannot be None")
            return None

        if not isinstance(value, self.field_type):
            raise ValueError(
                f"{self.field_name} must be {self.field_type}, not {type(value)}"
            )

        return self._validate(value)

    def _validate(self, value: Any) -> Any:
        return value


class CharField(Field):
    def __init__(self, required: bool = False, nullable: bool = True):
        super().__init__(required=required, nullable=nullable, field_type=str)

class EmailField(CharField):
    def _validate(self, value: str) -> str:
        if '@' not in value:
            raise ValueError(f"{self.field_name} must contain '@'")
        return value

class PhoneField(Field):
    def __init__(self, required: bool = False, nullable: bool = True):
        super().__init__(required=required, nullable=nullable, field_type=(str))

    def _validate(self, value: Union[str, int]) -> str:
        str_value = str(value)
        if len(str_value) != 11 or not str_value.startswith('7'):
            raise ValueError(f"{self.field_name} must be 11 digits and start with 7")
        return str_value

class DateField(Field):
    def __init__(self, required: bool = False, nullable: bool = True):
        super().__init__(required=required, nullable=nullable, field_type=str)

    def _validate(self, value: str) -> date:
        try:
            parsed_date = datetime.strptime(value, '%d.%m.%Y').date()
        except ValueError:
            raise ValueError(f"{self.field_name} must be in DD.MM.YYYY format")

        today = date.today()
        age = today.year - parsed_date.year - (
                (today.month, today.day) < (parsed_date.month, parsed_date.day)
        )
        if age > 70:
            raise ValueError(f"{self.field_name} must be less than 70 years ago")

        return parsed_date


class BirthDayField(DateField):
    pass


class GenderField(Field):
    def __init__(self, required: bool = False, nullable: bool = True):
        super().__init__(required=required, nullable=nullable, field_type=int)

    def _validate(self, value: int) -> int:
        if value not in {0, 1, 2}:
            raise ValueError(f"{self.field_name} must be 0, 1 or 2")
        return value


class ClientIDsField(Field):
    def __init__(self, required: bool = True, nullable: bool = False):
        super().__init__(required=required, nullable=nullable, field_type=list)

    def _validate(self, value: list) -> List[int]:
        if not value:
            raise ValueError(f"{self.field_name} cannot be empty")

        validated_ids = []
        for item in value:
            if not isinstance(item, int):
                raise ValueError(f"All ids in {self.field_name} must be integers")
            validated_ids.append(item)

        return validated_ids


class ArgumentFileField(Field):
    def __init__(self, required: bool = False, nullable: bool = False):
        super().__init__(required=required, nullable=nullable, field_type=dict)
