from yaddle import loads


def test_loads_enum():
    input = "test"
    expected = {'enum': ['test']}
    assert loads(input) == expected

    input = 'admin | author | "role with space "'
    expected = {'enum': ['admin', 'author', 'role with space ']}
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
    expected = {'type': "integer",
                "minimum": 1,
                "maximum": 9}
    assert loads(input) == expected

    input = "int{1,}"
    expected = {'type': "integer",
                "minimum": 1}
    assert loads(input) == expected

    input = "int{,2}"
    expected = {'type': "integer",
                "maximum": 2}
    assert loads(input) == expected


def test_loads_ref():
    input = """@location"""
    expected = {'$ref': '#/definitions/location'}
    assert loads(input) == expected


def test_loads_anyOf():
    input = """@location / @vector"""
    expected = {"anyOf": [
        {'$ref': '#/definitions/location'},
        {'$ref': '#/definitions/vector'}]}
    assert loads(input) == expected


def test_loads_allOf():
    input = """@location & @vector"""
    expected = {"allOf": [
        {'$ref': '#/definitions/location'},
        {'$ref': '#/definitions/vector'}]}
    assert loads(input) == expected


def test_loads_oneOf():
    input = """@location | @vector"""
    expected = {"oneOf": [
        {'$ref': '#/definitions/location'},
        {'$ref': '#/definitions/vector'}]}
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
                    "oneOf": [
                        {"type": "string",
                         "maxLength": 9},
                        {"type": "integer"}]
                },
                "maxItems": 1}
    assert loads(input) == expected


def test_loads_object():
    input = """role: str
active?: bool
null?: null
name: str
..."""
    expected = {'type': 'object',
                'properties': {'role': {'type': "string"},
                               "name": {"type": "string"},
                               "null": {"type": "null"},
                               "active": {"type": "boolean"}},
                'required': ["role", "name"]}
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
                'definitions': {
                    "location": {
                        "type": "object",
                        "properties": {
                            "x": {"type": "number"},
                            "y": {"type": "number"}},
                        "required": ["x", "y"],
                        "additionalProperties": False}
                },
                'properties': {'start': {'$ref': "#/definitions/location"},
                               'end': {'$ref': "#/definitions/location"}},
                'required': ["start", "end"],
                "additionalProperties": False}
    assert loads(input) == expected


def test_mount_point():
    input = """
@diskDevice:
    type: disk
    device: /^/dev/[^/]+(/[^/]+)*$/
@diskUUID:
    type: disk
    label: /^[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}$/
@nfs:
    type: nfs
    remotePath: /^(/[^/]+)+$/
    server: %hostname | %ipv4 | %ipv6
@tmpfs:
    type: tmpfs
    sizeInMB: int{16,512}

storage: @diskDevice | @diskUUID | @nfs | @tmpfs
fstype?: ext3 | ext4 | btrfs
options?: [str]{1,}!
readonly?: bool
...
"""
    expected = {
        # "id": "http://some.site.somewhere/entry-schema#",
        # "$schema": "http://json-schema.org/draft-04/schema#",
        # "description": "schema for an fstab entry",
        "type": "object",
        "required": ["storage"],
        "properties": {
            "storage": {
                # "type": "object",
                "oneOf": [
                    {"$ref": "#/definitions/diskDevice"},
                    {"$ref": "#/definitions/diskUUID"},
                    {"$ref": "#/definitions/nfs"},
                    {"$ref": "#/definitions/tmpfs"}
                ]
            },
            "fstype": {
                "enum": ["ext3", "ext4", "btrfs"]
            },
            "options": {
                "type": "array",
                "minItems": 1,
                "items": {"type": "string"},
                "uniqueItems": True
            },
            "readonly": {"type": "boolean"}
            },
        "definitions": {
            "diskDevice": {
                "type": "object",
                "properties": {
                    "type": {"enum": ["disk"]},
                    "device": {
                        "type": "string",
                        "pattern": "^/dev/[^/]+(/[^/]+)*$"
                    }
                },
                "required": ["type", "device"],
                "additionalProperties": False
            },
            "diskUUID": {
                "type": "object",
                "properties": {
                    "type": {"enum": ["disk"]},
                    "label": {
                        "type": "string",
                        "pattern": "^[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}$"  # noqa
                    }
                },
                "required": ["type", "label"],
                "additionalProperties": False
            },
            "nfs": {
                "type": "object",
                "properties": {
                    "type": {"enum": ["nfs"]},
                    "remotePath": {
                        "type": "string",
                        "pattern": "^(/[^/]+)+$"
                    },
                    "server": {
                        # "type": "string",
                        "oneOf": [
                            {"format": "hostname"},
                            {"format": "ipv4"},
                            {"format": "ipv6"}
                        ]
                }
            },
                "required": ["type", "remotePath", "server"],
                "additionalProperties": False
            },
            "tmpfs": {
                "type": "object",
                "properties": {
                    "type": {"enum": ["tmpfs"]},
                    "sizeInMB": {
                        "type": "integer",
                        "minimum": 16,
                        "maximum": 512
                    }
            },
                "required": ["type", "sizeInMB"],
                "additionalProperties": False
            }
    }}
    assert loads(input) == expected
