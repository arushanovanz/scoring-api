import datetime
import hashlib
from .model import ClientIDsField, CharField, DateField, EmailField, GenderField, PhoneField, BirthDayField, \
    ArgumentFileField, Field

SALT = "Otus"
ADMIN_LOGIN = "admin"
ADMIN_SALT = "42"

UNKNOWN = 0
MALE = 1
FEMALE = 2

class Request:
    account = CharField(required=False, nullable=True)
    login = CharField(required=True, nullable=True)
    token = CharField(required=True, nullable=True)
    arguments = ArgumentFileField(required=True, nullable=True)
    method = CharField(required=True, nullable=False)

    def __init__(self, data):
        self.login = data['body']['login']
        self.token = data['body']['token']
        self.method = data['body']['method']
        self.account = data['body'].get('account')
        self.arguments = data['body'].get('arguments', {})

        if not all([self.login, self.token, self.method]):
            raise ValueError("Missing required fields")

        if self.method not in ["clients_interests", "online_score"]:
                raise ValueError(f'Invalid method "{self.method}"')

    @property
    def is_admin(self):
        return self.login == ADMIN_LOGIN


class ClientsInterestsRequest(object):
    client_ids = ClientIDsField(required=True)
    date = DateField(required=False, nullable=True)

    def __init__(self, arguments):
        self.client_ids = arguments.get('client_ids')
        self.date = arguments.get('date')

        if not isinstance(self.client_ids, list) or not self.client_ids:
            raise ValueError("client_ids must be a non-empty list")

        if not all(isinstance(x, int) for x in self.client_ids):
            raise ValueError("All client_ids must be integers")

        if self.date and not self._validate_date(self.date):
            raise ValueError("Invalid date format. Use DD.MM.YYYY")


    def _validate_date(self, date_str):
        try:
            datetime.datetime.strptime(date_str, "%d.%m.%Y")
            return True
        except ValueError:
            return False

class OnlineScoreRequest(object):
    first_name = CharField(required=False, nullable=True)
    last_name = CharField(required=False, nullable=True)
    email = EmailField(required=False, nullable=True)
    phone = PhoneField(required=False, nullable=True)
    birthday = BirthDayField(required=False, nullable=True)
    gender = GenderField(required=False, nullable=True)

    def __init__(self, arguments):
            for field_name, field in self.__class__.__dict__.items():
                if isinstance(field, Field):
                    field.field_name = field_name

            for field_name, field in self.__class__.__dict__.items():
                if isinstance(field, Field):
                    value = arguments.get(field_name)
                    setattr(self, field_name, field.validate(value))

            has_pairs = [
                bool(self.phone and self.email),
                bool(self.first_name and self.last_name),
                bool(self.gender is not None and self.birthday)
            ]

            if not any(has_pairs):
                raise ValueError("Requires at least one pair: phone-email, first_name-last_name, or gender-birthday")


def check_auth(request_data):
    if isinstance(request_data, dict):

        body = request_data.get('body', {})
        login = body.get('login')
        is_admin = login == ADMIN_LOGIN

        if is_admin:
            digest = hashlib.sha512(
                (datetime.datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT).encode('utf-8')).hexdigest()
        else:
            account = body.get('account', '')
            login = body.get('login', '')
            digest = hashlib.sha512((account + login + SALT).encode('utf-8')).hexdigest()

        return digest == body.get('token')
    else:

        if request_data.is_admin:
            digest = hashlib.sha512(
                (datetime.datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT).encode('utf-8')).hexdigest()
        else:
            digest = hashlib.sha512((request_data.account + request_data.login + SALT).encode('utf-8')).hexdigest()
        return digest == request_data.token