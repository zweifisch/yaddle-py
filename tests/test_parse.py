from yaddle import *  # noqa
import pytest


def test_tokenize():
    input = """user:
    name: str{3,20}
    id: str"""
    expected = ["NAME", "OP", "NL",
                "INDENT", "NAME", "OP",
                "NAME", "OP", "NUMBER", "OP", "NUMBER", "OP", "NL",
                "NAME", "OP", "NAME", "NL", "DEDENT"]
    assert list(map(lambda x: x.type, tokenize(input))) == expected

    input = '"str\\"ing" "more"'
    expected = ["STRING", "STRING", "NL"]
    assert list(map(lambda x: x.type, tokenize(input))) == expected

    input = """
    

        
"""
    expected = ["NL"]
    assert list(map(lambda x: x.type, tokenize(input))) == expected


def test_bad_indentation():
    with pytest.raises(Exception) as e:
        parse(tokenize("""user:
    name: str
       id: str"""))
    assert "Bad indentation at 3,1" == str(e.value)


def test_parse_enum():
    input = 'admin | author | "role with space"'
    assert parse(tokenize(input)) == ("enum", ["admin", "author",
                                               "role with space"])

    input = 'c | 1 | -10.1 | 0 | true | false | null | "null" | "0.1"'
    expected = ("enum", ["c", 1, -10.1, 0, True, False, None, "null", "0.1"])
    assert parse(tokenize(input)) == expected


def test_parse_bool():
    input = "bool"
    assert parse(tokenize(input)) == ("boolean", None)


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

    input = "int{2,9,3}"
    assert parse(tokenize(input)) == ("integer", (2, 9, 3))

    input = "int"
    assert parse(tokenize(input)) == ("integer", None)


def test_parse_array():
    input = "[]"
    assert parse(tokenize(input)) == ("array", ([], None, None))

    input = "[num{1,100}]"
    expected = ("array",
                ([("number", (1, 100, None))], None, None))
    assert parse(tokenize(input)) == expected

    input = "[num | str]{2,10}"
    expected = ("array", ([('oneof',
                            [("number", None), ("string", (None, None))])],
                          (2, 10), None))
    assert parse(tokenize(input)) == expected

    input = "[@position, str | int]"
    expected = ("array", ([("ref", "position"),
                           ("oneof", [("string", (None, None)),
                                      ("integer", None)])],
                          None, None))
    assert parse(tokenize(input)) == expected


def test_parse_object():
    input = "name: str{3,20}"
    assert parse(tokenize(input)) == ("object",
                                      ({"name": ("string", ((3, 20), None))},
                                       ["name"], True, {}))

    input = """name: str{3,20}
id: str{32,32}"""
    assert parse(tokenize(input)) == ("object",
                                      ({"name": ("string", ((3, 20), None)),
                                        "id": ("string", ((32, 32), None))},
                                       ["name", "id"], True, {}))

    input = """name?: str{3,20}
id: str{32,32}
..."""
    assert parse(tokenize(input)) == ("object",
                                      ({"name": ("string", ((3, 20), None)),
                                        "id": ("string", ((32, 32), None))},
                                       ["id"], False, {}))

    input = """location:
    x: str{12,12}
    y: str{12,12}"""
    expected = ("object",
                ({"location": ("object",
                               ({"x": ("string", ((12, 12), None)),
                                 "y": ("string", ((12, 12), None))},
                                ["x", "y"], True, {}))},
                 ["location"], True, {}))
    assert parse(tokenize(input)) == expected

    input = """root:
    parent:
        child: str
        child2: str"""
    expected = ("object",
                ({"root": ("object",
                           ({"parent": ("object",
                                        ({"child": ("string", (None, None)),
                                          "child2": ("string", (None, None))},
                                         ["child", "child2"], True, {}))},
                            ["parent"], True, {}))},
                 ["root"], True, {}))
    assert parse(tokenize(input)) == expected

    input = """root:
    parent:
        child:
            child2: null"""
    expected = ("object",
                ({"root":
                  ("object",
                   ({"parent":
                     ("object",
                      ({"child":
                        ("object",
                         ({"child2":
                           ("null", None)},
                          ["child2"], True, {}))},
                       ["child"], True, {}))},
                    ["parent"], True, {}))},
                 ["root"], True, {}))
    assert parse(tokenize(input)) == expected

    input = """
root:
    parent:
        child: str
    parent2: str
    """
    expected = ("object",
                ({"root": ("object",
                           ({"parent": ("object",
                                        ({"child": ("string", (None, None))},
                                         ["child"], True, {})),
                             "parent2": ("string", (None, None))},
                            ["parent", "parent2"], True, {}))},
                 ["root"], True, {}))
    assert parse(tokenize(input)) == expected


def test_parse_ref():
    input = "@position"
    assert parse(tokenize(input)) == ("ref", "position")
