from yaddle import *  # noqa


def test_tokenize():
    input = """user:
    name: str{3,20}
    id: str
"""
    expected = ["NAME", "OP", "NL",
                "INDENT", "NAME", "OP", "SPACE",
                "NAME", "OP", "NUMBER", "OP", "NUMBER", "OP", "NL",
                "NAME", "OP", "SPACE", "NAME", "NL", "DEDENT"]
    assert map(lambda x: x.type, tokenize(input)) == expected


def test_parse_enum():
    input = "admin | author | role with space"
    assert parse(tokenize(input)) == ("enum", ["admin", "author",
                                               "role with space"])


def test_parse_string():
    input = "str{3,20}"
    assert parse(tokenize(input)) == ("string", ((3, 20), None))

    input = "str{,20}"
    assert parse(tokenize(input)) == ("string", ((None, 20), None))

    input = "str{3,}"
    assert parse(tokenize(input)) == ("string", ((3, None), None))

    input = "str{3,20} /[a-zA-Z]+/"
    assert parse(tokenize(input)) == ("string", ((3, 20), "[a-zA-Z]+"))

    input = "str"
    assert parse(tokenize(input)) == ("string", (None, None))

    input = "/[a-z]/"
    assert parse(tokenize(input)) == ("string", (None, "[a-z]"))

    input = "{3,}/[a-z]/"
    assert parse(tokenize(input)) == ("string", ((3, None), "[a-z]"))


def test_parse_number():
    input = "num"
    assert parse(tokenize(input)) == ("number", None)

    input = "num{2,3}"
    assert parse(tokenize(input)) == ("number", (2, 3, None))

    input = "int{2,3}"
    assert parse(tokenize(input)) == ("number", (2, 3, 1))

    input = "int"
    assert parse(tokenize(input)) == ("number", (None, None, 1))


def test_parse_array():
    input = "[]"
    assert parse(tokenize(input)) == ("array",
                                      ([], None))
    input = "[num{1,100}]"
    assert parse(tokenize(input)) == ("array",
                                      ([("number", (1, 100, None))], None))
    input = "[num, str]{2,10}"
    assert parse(tokenize(input)) == ("array", ([
        ("number", None),
        ("string", (None, None)),
    ], (2, 10)))


def test_parse_object():
    input = "name: str{3,20}"
    assert parse(tokenize(input)) == ("object",
                                      {"name": ("string", ((3, 20), None))})

    input = """name: str{3,20}
id: str{32,32}"""
    assert parse(tokenize(input)) == ("object",
                                      {"name": ("string", ((3, 20), None)),
                                       "id": ("string", ((32, 32), None))})

    input = """location:
    x: str{12,12}
    y: str{12,12}"""
    expected = ("object",
                {"location": ("object",
                              {"x": ("string", ((12, 12), None)),
                               "y": ("string", ((12, 12), None))})})
    assert parse(tokenize(input)) == expected

    input = """root:
    parent:
        child: str
        child2: str
root2: str"""
    expected = ("object",
                {"root": ("object",
                          {"parent": ("object",
                                      {"child": ("string", (None, None)),
                                       "child2": ("string", (None, None))})}),
                 "root2": ("string", (None, None))})
    assert parse(tokenize(input)) == expected
