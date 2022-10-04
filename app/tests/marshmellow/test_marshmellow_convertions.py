from datetime import datetime
import uuid
from app.tests.fixtures.data_fixtures import Client, User
from app.tests.fixtures.marshmellow_fixtures import UserSchema, UserSchemaWichPostLoad, CleintSchema, CleintSchemaFlat
from pytest_dictsdiff import check_objects
from marshmallow import INCLUDE, Schema, ValidationError, fields
import datetime as dt


class TestSerializing():


    def test_dump_to_dict(self, user_1:User)->None:
        schema = UserSchema()
        result_dict = schema.dump(user_1)
        assert isinstance(result_dict, dict)

    def test_dump_to_json(self, user_1:User)->None:
        schema = UserSchema()
        result_str_json = schema.dumps(user_1)
        assert isinstance(result_str_json, str)

    def test_dump_to_dict_part(self, user_1:User)->None:
        #You can also exclude fields by passing in the exclude parameter.
        schema = UserSchema(only=("name", "email"))
        result_dict = schema.dump(user_1)

        assert "name" in result_dict.keys()
        assert "email" in result_dict.keys()
        assert "created_at" not in result_dict.keys()

    def test_dump_from_object_to_dict_many(self)->None:
        user1 = User(name="Mick", email="mick@stones.com")
        user2 = User(name="Keith", email="keith@stones.com")
        users = [user1, user2]
        schema = UserSchemaWichPostLoad(many=True) 
        result_dict = schema.dump(users)# OR UserSchemaWichPostLoad().dump(users, many=True)

        assert isinstance(result_dict, list)
        assert isinstance(result_dict[0], dict)



class TestDeserializing():


    def test_deserializing_from_dict_to_dict_wich_type(self, user_2_dict:dict)->None:
        schema = UserSchema()
        result_dict = schema.load(user_2_dict)

        assert isinstance(result_dict, dict)
        assert isinstance(result_dict["created_at"], datetime)


    def test_deserializing_from_dict_to_object(self, user_2_dict_wichout_created_at:dict)->None:
        schema = UserSchemaWichPostLoad()
        result_user = schema.load(user_2_dict_wichout_created_at)

        assert isinstance(result_user, User)

class TestValidating():

    def test_validating_error(self):
        try:
            result = UserSchema().load({"name": "John", "email": "foo"})
        except ValidationError as err:
            assert 'email' in err.messages.keys()
            assert err.messages["email"] == ['Not a valid email address.']

            assert 'name' in err.valid_data
            assert err.valid_data["name"] == "John"

    def test_valdating_wich_own_validator(self):
        # have some already exist validators https://marshmallow.readthedocs.io/en/stable/marshmallow.validate.html#api-validators
        # validators might be a memeber function
        # class ItemSchema(Schema):
        #     quantity = fields.Integer()

        #     @validates("quantity")
        #     def validate_quantity(self, value):
        #         if value < 0:
        #             raise ValidationError("Quantity must be greater than 0.")
        #         if value > 30:
        #             raise ValidationError("Quantity must not be greater than 30.")
        def validate_quantity(n):
            if n < 0:
                raise ValidationError("Quantity must be greater than 0.")
            if n > 30:
                raise ValidationError("Quantity must not be greater than 30.")
        class ItemSchema(Schema):
            quantity = fields.Integer(validate=validate_quantity)

        in_data_incorrect = {"quantity": 31}
        try:
            result = ItemSchema().load(in_data_incorrect)
            assert False
        except ValidationError as err:
            assert err.messages['quantity'] == ["Quantity must not be greater than 30."]

        in_data_correct = {"quantity": 15}
        result = ItemSchema().load(in_data_correct)
        assert result is not None

    def test_validate_reuquries_and_cutom_message(self):
        class UserSchema(Schema):
            name = fields.String(required=True)
            age = fields.Integer(required=True, error_messages={"required": "Age is required."})
            city = fields.String(
                required=True,
                error_messages={"required": {"message": "City required", "code": 400}},
            )
            email = fields.Email()


        try:
            result = UserSchema().load({"email": "foo@bar.com"})
            assert False
        except ValidationError as err:
            assert err.messages['age'] == ['Age is required.']
            # {'age': ['Age is required.'],
            # 'city': {'code': 400, 'message': 'City required'},
            # 'name': ['Missing data for required field.']}

    def test_defalut_values(self):
        class UserSchema(Schema):
            id = fields.UUID(load_default=uuid.uuid1)
            birthdate = fields.DateTime(dump_default=dt.datetime(2017, 9, 29))


        result = UserSchema().load({})
        assert isinstance(result.get('id'), uuid.UUID)
        # {'id': UUID('337d946c-32cd-11e8-b475-0022192ed31b')}
        result = UserSchema().dump({})
        assert isinstance(result.get('birthdate'), str)
        # {'birthdate': '2017-09-29T00:00:00+00:00'}

    def test_uncnown_field(self):
        # This behavior can be modified with the unknown option, which accepts one of the following:
        #     RAISE (default): raise a ValidationError if there are any unknown fields
        #     EXCLUDE: exclude unknown fields
        #     INCLUDE: accept and include the unknown fields

        class UserSchema(Schema):
            class Meta:
                unknown = INCLUDE
        # or
        schema = UserSchema(unknown=INCLUDE)

        # or
        data = {"test_uncnow_field":"value_uncnown_field"}
        resutl = UserSchema().load(data, unknown=INCLUDE)
        assert resutl == {"test_uncnow_field":"value_uncnown_field"}

    def test_specific_keys(self):
        class UserSchema(Schema):
            name = fields.String()
            email = fields.Email(data_key="emailAddress")


        s = UserSchema()

        data = {"name": "Mike", "email": "foo@bar.com"}
        result = s.dump(data)
        assert 'emailAddress' in result.keys()
        # {'name': u'Mike',
        # 'emailAddress': 'foo@bar.com'}

        data = {"name": "Mike", "emailAddress": "foo@bar.com"}
        result = s.load(data)
        assert 'email' in result.keys()
        # {'name': u'Mike',
        # 'email': 'foo@bar.com'}

    def test_create_field_form_class_object(self, user_1:User):
        # When your model has many attributes, specifying the field type for every attribute can get repetitive, especially when many of the attributes are already native Python datatypes.
        # The fields option allows you to specify implicitly-created fields. Marshmallow will choose an appropriate field type based on the attribute’s type.
        # Let’s refactor our User schema to be more concise.

        class UserSchema(Schema):
            uppername = fields.Function(lambda obj: obj.name.upper())

            class Meta:
                fields = ("name", "email", "created_at", "uppername")
                # or
                # No need to include 'uppername'
                # additional = ("name", "email", "created_at")

        my_shema = UserSchema()
        result = my_shema.dump(user_1)
        assert result is not None

class TestNestedFIelds():

    def test_nested_scheme(self, clien_wich_two_tasks:Client):
        schema = CleintSchema()
        result = schema.dump(clien_wich_two_tasks)
        assert isinstance(result, dict)
        assert len(result['tasks']) == 2
        assert isinstance(result['tasks'], list)
        assert isinstance(result['tasks'][0], dict)

    def test_nested_flat_data(self, clien_wich_two_tasks:Client):
        schema = CleintSchemaFlat()
        result = schema.dump(clien_wich_two_tasks)
        assert isinstance(result, dict)
        # flat list, only contain field in Pluck
        assert isinstance(result['tasks'], list)
        assert isinstance(result['tasks'][0], str)


class TestCustomFields():
    #https://marshmallow.readthedocs.io/en/stable/custom_fields.html

    def test_cutom_field_class(self, user_2_dict:dict):
        class PinCode(fields.Field):
            """Field that serializes to a string of numbers and deserializes
            to a list of numbers.
            """

            def _serialize(self, value, attr, obj, **kwargs):
                if value is None:
                    return ""
                return "".join(str(d) for d in value)

            def _deserialize(self, value, attr, data, **kwargs):
                try:
                    return [int(c) for c in value]
                except ValueError as error:
                    raise ValidationError("Pin codes must contain only digits.") from error


        class UserSchema(Schema):
            name = fields.String()
            email = fields.String()
            created_at = fields.DateTime()
            pin_code = PinCode()

        schema = UserSchema()
        user_2_dict.update({"pin_code":'12345'})
        dict_value = schema.load(user_2_dict)
        assert isinstance(dict_value["pin_code"], list)
        assert dict_value["pin_code"] == [1,2,3,4,5]
        repf_value = schema.dump(dict_value)
        assert isinstance(repf_value["pin_code"], str)
        assert repf_value["pin_code"] == "12345"

    def test_custom_fields_function(self, user_2_dict:dict):
        class UserSchema(Schema):
            income = fields.Integer()
            debt = fields.Integer()
            # `Method` takes a method name (str), Function takes a callable
            balance = fields.Method("get_balance", deserialize="load_balance")

            def get_balance(self, obj):
                return obj.get('income', 0) - obj.get('debt', 0)

            def load_balance(self, value):
                return float(value)

        input_data = {'income':100, 'debt':30, 'balance':70}
        schema = UserSchema()
        data_dict = schema.load(input_data)
        assert isinstance(data_dict["balance"], float)

        input_data = {'income':100, 'debt':30}
        output_data = schema.dump(input_data)
        assert isinstance(output_data['balance'], int)
        assert output_data['balance'] == 70

    def test_customising_error(self, user_2_dict:dict):
        class MyDate(fields.Date):
            default_error_messages = {"invalid": "Please provide a valid date."}

        class UserSchema(Schema):
            name = fields.String()
            email = fields.Email(error_messages={"invalid": "Enter valid e-mail."})
            created_at = MyDate()

        schema = UserSchema()
        user_2_dict['created_at'] = "not_valid"
        user_2_dict['email'] = "email_not_valid"
        dict_error_validations = schema.validate(user_2_dict)
        assert len(dict_error_validations) == 2
        assert dict_error_validations['email'][0] == "Enter valid e-mail."
        assert dict_error_validations['created_at'][0] == "Please provide a valid date."
