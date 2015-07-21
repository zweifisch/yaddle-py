from yaddle import loads


def test_loads_enum():
    input = "admin | author | role with space"
    expected = {'enum': ['admin', 'author', 'role with space']}
    assert loads(input) == expected


def test_loads_string():
    input = "str{2,30}"
    expected = {'type': "string",
                "minLength": 2,
                "maxLength": 30}
    assert loads(input) == expected

    input = "str{2,}"
    expected = {'type': "string",
                "minLength": 2}
    assert loads(input) == expected

    input = "str{,30}"
    expected = {'type': "string",
                "maxLength": 30}
    assert loads(input) == expected

    input = "/[?{}]/"
    expected = {'type': "string",
                "pattern": "[?{}]"}
    assert loads(input) == expected

    input = "str/[?{}]/"
    expected = {'type': "string",
                "pattern": "[?{}]"}
    assert loads(input) == expected


def test_load_number():
    input = "num{1,9,3}"
    expected = {'type': "number",
                "minimum": 1,
                "maximum": 9,
                "multipleOf": 3}
    assert loads(input) == expected

    input = "int{1,9}"
    expected = {'type': "number",
                "minimum": 1,
                "maximum": 9,
                "multipleOf": 1}
    assert loads(input) == expected

    input = "int"
    expected = {'type': "number",
                "multipleOf": 1}
    assert loads(input) == expected

    input = "int{1,}"
    expected = {'type': "number",
                "minimum": 1,
                "multipleOf": 1}
    assert loads(input) == expected

    input = "int{,2}"
    expected = {'type': "number",
                "maximum": 2,
                "multipleOf": 1}
    assert loads(input) == expected


def test_loads_ref():
    input = """@location"""
    expected = {'$ref': '#/definations/location'}
    assert loads(input) == expected


def test_loads_array():
    input = """[]"""
    expected = {'type': 'array'}
    assert loads(input) == expected

    input = """[]{1,9}"""
    expected = {'type': 'array',
                "minItems": 1,
                "maxItems": 9}
    assert loads(input) == expected

    input = """[]{1,}"""
    expected = {'type': 'array',
                "minItems": 1}
    assert loads(input) == expected

    input = """[str]"""
    expected = {'type': 'array',
                "items": {"type": "string"}}
    assert loads(input) == expected

    input = """[str{,9} | int]{,1}"""
    expected = {'type': 'array',
                "items": {
                    "anyOf": [
                        {"type": "string",
                         "maxLength": 9},
                        {"type": "number",
                         "multipleOf": 1}]
                },
                "maxItems": 1}
    assert loads(input) == expected


def test_loads_object():
    input = """role: str
name: str
..."""
    expected = {'type': 'object',
                'properties': {'role': {'type': "string"},
                               "name": {"type": "string"}},
                'required': ["role", "name"],
                "additionalProperties": True}
    assert loads(input) == expected

    input = """role: str
location?:
    x: num
    y: num"""
    expected = {'type': 'object',
                'required': ["role"],
                "additionalProperties": False,
                'properties': {'role': {'type': "string"},
                               "location":
                               {"type": "object",
                                "required": ["x", "y"],
                                "additionalProperties": False,
                                "properties": {
                                    "x": {"type": "number"},
                                    "y": {"type": "number"}}}}}
    assert loads(input) == expected

    input = """
@location:
    x: num
    y: num
start: @location
end: @location
"""
    expected = {'type': 'object',
                'definations': {
                    "location": {
                        "type": "object",
                        "properties": {
                            "x": {"type": "number"},
                            "y": {"type": "number"}},
                        "required": ["x", "y"],
                        "additionalProperties": False}
                },
                'properties': {'start': {'$ref': "#/definations/location"},
                               'end': {'$ref': "#/definations/location"}},
                'required': ["start", "end"],
                "additionalProperties": False}
    assert loads(input) == expected
