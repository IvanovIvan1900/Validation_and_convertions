from datetime import datetime
from app.tests.fixtures.data_fixtures import User
from app.tests.fixtures.marshmellow_fixtures import UserSchema, UserSchemaWichPostLoad
from pytest_dictsdiff import check_objects


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

    