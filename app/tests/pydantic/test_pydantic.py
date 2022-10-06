from datetime import date, datetime, time, timedelta
from typing import Generic, Literal, TypeVar
from uuid import UUID, uuid4
from pydantic import (
    BaseModel,
    Field,
    PydanticValueError,
    ValidationError,
    conint,
    constr,
    parse_obj_as,
    root_validator,
    validator,
)
import pytest


class TestModel:
    def test_model_fields(self):
        class User(BaseModel):
            id: int  # requered
            name = "Jane Doe"  # not requered

        user_1 = User(id=124)
        assert isinstance(user_1, User)
        assert user_1.id == 124
        assert user_1.name == "Jane Doe"

        user_1 = User(id=124.45)  # cast data
        assert user_1.id == 124

        user_1 = User(id=124.45, name="Test name")
        assert user_1.name == "Test name"

    def test_model_function(self):
        # https://pydantic-docs.helpmanual.io/usage/models/ - many functins
        class User(BaseModel):
            id: int  # requered
            name = "Jane Doe"  # not requered

        user_1 = User(id=124)
        json = user_1.json()
        assert isinstance(json, str)

        dict_data = user_1.dict()
        assert isinstance(dict_data, dict)

    def test_recursive_models(self):
        class Foo(BaseModel):
            count: int
            size: float | None = None

        class Bar(BaseModel):
            apple = "x"
            banana = "y"

        class Spam(BaseModel):
            foo: Foo
            bars: list[Bar]

        m = Spam(foo={"count": 4}, bars=[{"apple": "x1"}, {"apple": "x2"}])
        assert isinstance(m, Spam)
        # > foo=Foo(count=4, size=None) bars=[Bar(apple='x1', banana='y'),
        # > Bar(apple='x2', banana='y')]
        # print(m.dict())
        """
        {
            'foo': {'count': 4, 'size': None},
            'bars': [
                {'apple': 'x1', 'banana': 'y'},
                {'apple': 'x2', 'banana': 'y'},
            ],
        }
        """

    def test_orm_mode(self):
        from sqlalchemy import Column, Integer, String
        from sqlalchemy.dialects.postgresql import ARRAY
        from sqlalchemy.ext.declarative import declarative_base
        from pydantic import BaseModel, constr

        Base = declarative_base()

        class CompanyOrm(Base):
            __tablename__ = "companies"
            id = Column(Integer, primary_key=True, nullable=False)
            public_key = Column(String(20), index=True, nullable=False, unique=True)
            name = Column(String(63), unique=True)
            domains = Column(ARRAY(String(255)))

        class CompanyModel(BaseModel):
            id: int
            public_key: constr(max_length=20)
            name: constr(max_length=63)
            domains: list[constr(max_length=255)]

            class Config:
                orm_mode = True

        co_orm = CompanyOrm(
            id=123,
            public_key="foobar",
            name="Testing",
            domains=["example.com", "foobar.com"],
        )
        assert isinstance(co_orm, CompanyOrm)
        # > <models_orm_mode_3_9.CompanyOrm object at 0x7fb20cc17790>
        co_model = CompanyModel.from_orm(co_orm)
        assert isinstance(co_model, CompanyModel)
        # > id=123 public_key='foobar' name='Testing' domains=['example.com',
        # > 'foobar.com']


class TestValidation:
    # You can access these errors in several ways:
    # e.errors()
    #     method will return list of errors found in the input data.
    # e.json()
    #     method will return a JSON representation of errors.
    # str(e)
    #     method will return a human readable representation of the errors.
    # Each error object contains:
    # loc
    #     the error's location as a list. The first item in the list will be the field where the error occurred,
    # and if the field is a sub-model, subsequent items will be present to indicate the nested location of the error.
    # type
    #     a computer-readable identifier of the error type.
    # msg
    #     a human readable explanation of the error.
    # ctx
    #     an optional object which contains values required to render the error message.

    def test_error_handling(self):
        class Model(BaseModel):
            is_required: float
            gt_int: conint(gt=42)
            list_of_ints: list[int] = None
            a_float: float = None

        data = dict(
            list_of_ints=["1", 2, "bad"],
            a_float="not a float",
            recursive_model={"lat": 4.2, "lng": "New York"},
            gt_int=21,
        )

        # with pytest.raises(ValidationError) as ve:
        try:
            Model(**data)
            assert False
        except ValidationError as ve:
            assert len(ve.errors()) == 4

    def test_custom_validator_and_error(self):
        class NotABarError(PydanticValueError):
            code = "not_a_bar"
            msg_template = 'value is not "bar", got "{wrong_value}"'

        class Model(BaseModel):
            foo: str

            @validator("foo")
            def value_must_equal_bar(cls, v):
                if v != "bar":
                    raise NotABarError(wrong_value=v)
                return v

        try:
            Model(foo="ber")
        except ValidationError as e:
            assert len(e.errors()) == 1
            assert e.errors()[0]["msg"] == 'value is not "bar", got "ber"'
            assert e.errors()[0]["type"] == "value_error.not_a_bar"


class TestCreateModel:
    def test_create_model_generic(self):
        # честно говоря тема мутная, но важная
        from pydantic.generics import GenericModel

        DataT = TypeVar("DataT")

        class Error(BaseModel):
            code: int
            message: str

        class DataModel(BaseModel):
            numbers: list[int]
            people: list[str]

        class Response(GenericModel, Generic[DataT]):
            data: DataT | None
            error: Error | None

            @validator("error", always=True)
            def check_consistency(cls, v, values):
                if v is not None and values["data"] is not None:
                    raise ValueError("must not provide both data and error")
                if v is None and values.get("data") is None:
                    raise ValueError("must provide data or error")
                return v

        data = DataModel(numbers=[1, 2, 3], people=[])
        error = Error(code=404, message="Not found")

        assert Response[int](data=1).dict() == {"data": 1, "error": None}
        # > data=1 error=None
        assert Response[str](data="value").dict() == {"data": "value", "error": None}
        # > data='value' error=None
        assert Response[str](data="value").dict()
        # > {'data': 'value', 'error': None}
        assert Response[DataModel](data=data).dict() == {
            "data": {"numbers": [1, 2, 3], "people": []},
            "error": None,
        }
        """
        {
            'data': {'numbers': [1, 2, 3], 'people': []},
            'error': None,
        }
        """
        assert Response[DataModel](error=error).dict() == {
            "data": None,
            "error": {"code": 404, "message": "Not found"},
        }
        """
        {
            'data': None,
            'error': {'code': 404, 'message': 'Not found'},
        }
        """
        try:
            Response[int](data="value")
        except ValidationError as e:
            assert len(e.errors()) == 2
            """
            2 validation errors for Response[int]
            data
            value is not a valid integer (type=type_error.integer)
            error
            must provide data or error (type=value_error)
            """

    def test_requered_fields(self):
        # Here a, b and c are all required. However, use of the ellipses in b will not work well with mypy, and as of v1.0
        # should be avoided in most cases.
        class Model(BaseModel):
            a: int
            b: int = ...
            c: int = Field(...)

        with pytest.raises(ValidationError):
            Model(**{"a": 1, "b": 2})

        with pytest.raises(ValidationError):
            Model(**{"a": 1, "c": 3})

        with pytest.raises(ValidationError):
            Model(**{"b": 2, "c": 3})

        correct_data = Model(**{"a": 1, "b": 2, "c": 3})
        assert correct_data is not None

    def test_dinamically_default_value(self):
        class Model(BaseModel):
            uid: UUID = Field(default_factory=uuid4)
            updated: datetime = Field(default_factory=datetime.utcnow)

        data = Model()
        assert isinstance(data.uid, UUID)
        assert isinstance(data.updated, datetime)

    def test_parse_as(self):
        class Item(BaseModel):
            id: int
            name: str

        # `item_data` could come from an API call, eg., via something like:
        # item_data = requests.get('https://my-api.com/items').json()
        item_data = [{"id": 1, "name": "My Item"}]

        items = parse_obj_as(list[Item], item_data)
        assert len(items) == 1
        assert isinstance(items[0], Item)


class TestTypeFields:
    def test_union_field(self):
        # typing.Union also ignores order when defined, so Union[int, float] == Union[float, int]
        # which can lead to unexpected behaviour when combined with matching based on the Union type
        # order inside other type definitions, such as List and Dict types (because Python treats these
        #  definitions as singletons). For example, Dict[str, Union[int, float]] == Dict[str, Union[float, int]]
        # with the order based on the first time it was defined. Please note that this can also be affected by
        # third party libraries and their internal type definitions and the import orders.
        class User(BaseModel):
            id: int | str | UUID
            name: str

        user_01 = User(id=123, name="John Doe")
        assert isinstance(user_01.id, int)
        assert user_01.id == 123
        # > id=123 name='John Doe'
        user_02 = User(id="1234", name="John Doe")
        assert isinstance(user_02.id, int)
        assert user_02.id == 1234
        # > id=1234 name='John Doe'
        user_03_uuid = UUID("cf57432e-809e-4353-adbd-9d5c0d733868")
        user_03 = User(id=user_03_uuid, name="John Doe")
        assert isinstance(user_03.id, int)
        assert user_03.id == 275603287559914445491632874575877060712
        # > id=275603287559914445491632874575877060712 name='John Doe'
        # print(user_03.id)
        # > 275603287559914445491632874575877060712
        # print(user_03_uuid.int)
        # > 275603287559914445491632874575877060712

    def test_discriminated_union(self):
        class Cat(BaseModel):
            pet_type: Literal["cat"]
            meows: int

        class Dog(BaseModel):
            pet_type: Literal["dog"]
            barks: float

        class Lizard(BaseModel):
            pet_type: Literal["reptile", "lizard"]
            scales: bool

        class Model(BaseModel):
            pet: Cat | Dog | Lizard = Field(..., discriminator="pet_type")
            n: int

        result = Model(pet={"pet_type": "dog", "barks": 3.14}, n=1)
        assert isinstance(result.pet, Dog)
        # > pet=Dog(pet_type='dog', barks=3.14) n=1

        try:
            Model(pet={"pet_type": "dog"}, n=1)
            assert False
        except ValidationError as e:
            assert isinstance(e, ValidationError)
            """
            1 validation error for Model
            pet -> Dog -> barks
            field required (type=value_error.missing)
            """

        # def test_enum_str_and_int(self):
        #     class FruitEnum(str, enum):
        #         pear = "pear"
        #         banana = "banana"
        #         __metaclass__ = enum

        #     class ToolEnum(enum.IntEnum):
        #         spanner = 1
        #         wrench = 2

        #     class CookingModel(BaseModel):
        #         fruit: FruitEnum = FruitEnum.pear
        #         tool: ToolEnum = ToolEnum.spanner

        #     model = CookingModel()
        #     # > fruit=<FruitEnum.pear: 'pear'> tool=<ToolEnum.spanner: 1>
        #     print(CookingModel(tool=2, fruit="banana"))
        #     # > fruit=<FruitEnum.banana: 'banana'> tool=<ToolEnum.wrench: 2>
        #     try:
        #         CookingModel(fruit="other")
        #     except ValidationError as e:
        #         print(e)
        #         """
        #         1 validation error for CookingModel
        #         fruit
        #         value is not a valid enumeration member; permitted: 'pear', 'banana'
        #         (type=type_error.enum; enum_values=[<FruitEnum.pear: 'pear'>,
        #         <FruitEnum.banana: 'banana'>])
        #         """

    def test_date_time_fields(self):
        class Model(BaseModel):
            d: date = None
            dt: datetime = None
            t: time = None
            td: timedelta = None

        m = Model(
            d=1966280412345.6789,
            dt="2032-04-23T10:20:30.400+02:30",
            t=time(4, 8, 16),
            td="P3DT12H30M5S",
        )

        assert m.td == timedelta(days=3, seconds=45005)
        # print(m.dict())
        """
        {
            'd': datetime.date(2032, 4, 22),
            'dt': datetime.datetime(2032, 4, 23, 10, 20, 30, 400000,
        tzinfo=datetime.timezone(datetime.timedelta(seconds=9000))),
            't': datetime.time(4, 8, 16),
            'td': datetime.timedelta(days=3, seconds=45005),
        }
        """

    def test_type_var(self):
        Foobar = TypeVar("Foobar")
        BoundFloat = TypeVar("BoundFloat", bound=float)
        IntStr = TypeVar("IntStr", int, str)

        class Model(BaseModel):
            a: Foobar  # equivalent of ": Any"
            b: BoundFloat  # equivalent of ": float"
            c: IntStr  # equivalent of ": Union[int, str]"

        m = Model(a=[1], b=4.2, c="x")
        assert isinstance(m.a, list)
        # > a=[1] b=4.2 c='x'

        # a may be None and is therefore optional
        m2 = Model(b=1, c=1)
        assert m2.a is None
        # > a=None b=1.0 c=1

    def test_literal(self):
        class Pie(BaseModel):
            flavor: Literal["apple", "pumpkin"]

        Pie(flavor="apple")
        Pie(flavor="pumpkin")
        try:
            Pie(flavor="cherry")
            assert False
        except ValidationError as e:
            assert isinstance(e, ValidationError)
            """
            1 validation error for Pie
            flavor
            unexpected value; permitted: 'apple', 'pumpkin'
            (type=value_error.const; given=cherry; permitted=('apple', 'pumpkin'))
            """

    def test_constrains_field(self):
        # many, many type field https://pydantic-docs.helpmanual.io/usage/types/
        class Model(BaseModel):
            big_int: conint(gt=1000, lt=1024)  # from 1000 to 1024
            upper_str: constr(to_upper=True)
            short_str: constr(min_length=2, max_length=10)

        m = Model(big_int=1001, upper_str="UPPER", short_str="123")
        assert m is not None


class TestValidators:
    def test_validate(self):
        class UserModel(BaseModel):
            name: str
            username: str
            password1: str
            password2: str

            @validator("name")
            def name_must_contain_space(cls, v):
                if " " not in v:
                    raise ValueError("must contain a space")
                return v.title()

            @validator("password2")
            def passwords_match(cls, v, values, **kwargs):
                # values: a dict containing the name-to-value mapping of any previously-validated fields
                # **kwargs: if provided, this will include the arguments above not explicitly listed in the signature
                if "password1" in values and v != values["password1"]:
                    raise ValueError("passwords do not match")
                return v

            @validator("username")
            def username_alphanumeric(cls, v):
                assert v.isalnum(), "must be alphanumeric"
                return v

        user = UserModel(
            name="samuel colvin",
            username="scolvin",
            password1="zxcvbn",
            password2="zxcvbn",
        )
        assert user is not None
        # > name='Samuel Colvin' username='scolvin' password1='zxcvbn' password2='zxcvbn'

        try:
            UserModel(
                name="samuel",
                username="scolvin",
                password1="zxcvbn",
                password2="zxcvbn2",
            )
            assert False
        except ValidationError as e:
            assert isinstance(e, ValidationError)
            """
            2 validation errors for UserModel
            name
            must contain a space (type=value_error)
            password2
            passwords do not match (type=value_error)
            """

    def test_validate_entire_model(self):
        class UserModel(BaseModel):
            username: str
            password1: str
            password2: str

            @root_validator(pre=True)
            def check_card_number_omitted(cls, values):
                assert "card_number" not in values, "card_number should not be included"
                return values

            @root_validator
            def check_passwords_match(cls, values):
                pw1, pw2 = values.get("password1"), values.get("password2")
                if pw1 is not None and pw2 is not None and pw1 != pw2:
                    raise ValueError("passwords do not match")
                return values

        m = UserModel(username="scolvin", password1="zxcvbn", password2="zxcvbn")
        assert m is not None
        # > username='scolvin' password1='zxcvbn' password2='zxcvbn'
        try:
            UserModel(username="scolvin", password1="zxcvbn", password2="zxcvbn2")
        except ValidationError as e:
            assert isinstance(e, ValidationError)
            """
            1 validation error for UserModel
            __root__
            passwords do not match (type=value_error)
            """

        try:
            UserModel(
                username="scolvin",
                password1="zxcvbn",
                password2="zxcvbn",
                card_number="1234",
            )
        except ValidationError as e:
            assert isinstance(e, ValidationError)
            """
            1 validation error for UserModel
            __root__
            card_number should not be included (type=assertion_error)
            """

    def test_validate_dataclass(self):
        from pydantic.dataclasses import dataclass

        @dataclass
        class DemoDataclass:
            ts: datetime = None

            @validator("ts", pre=True, always=True)
            def set_ts_now(cls, v):
                return v or datetime.now()

        ddc = DemoDataclass()
        assert ddc is not None
        # > DemoDataclass(ts=datetime.datetime(2022, 9, 5, 18, 0, 25, 675255))
        ddc = DemoDataclass(ts="2017-11-08T14:00")
        assert ddc is not None
        assert isinstance(ddc.ts, datetime)
        # > DemoDataclass(ts=datetime.datetime(2017, 11, 8, 14, 0))


class TestModelConfig:

    pass
