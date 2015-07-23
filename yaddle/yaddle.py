from funcparserlib.parser import (some, a, many, skip, finished, maybe,
                                  forward_decl, oneplus)
from funcparserlib.lexer import make_tokenizer, Token


def tokenize(input):
    token_specs = [
        ('NAME', (r'[A-Za-z_][A-Za-z_0-9-]*',)),
        ('REGEXP', (r'/.*/',)),
        ('STRING', (r'"((\\")|[^"])*"',)),
        ('OP', (r'([{}\[\]?$:,|@%!/&]|\.{3})',)),
        ('NUMBER', (r'-?(0|[1-9]\d*)(\.\d+)?',)),
        ('COMMENT', (r'#.*',)),
        ('NL', (r'[\r\n]+([ \t]+[\r\n]+)*',)),
        ('SPACE', (r'[ \t]+',))
    ]
    return indentation(make_tokenizer(token_specs)(input + "\n"))


def indentation(tokens):
    "add indent/dedent and remove comments"
    newline = False
    level = 0
    indent_with = None
    for token in tokens:
        if token.type == "COMMENT":
            continue
        if token.type == "NL":
            newline = True
            yield token
        else:
            if newline:
                newline = False
                if token.type == "SPACE":
                    if not indent_with:
                        indent_with = token.value
                    indent_level = token.value.count(indent_with)
                    if indent_level * indent_with != token.value:
                        raise Exception("Bad indentation at %d,%d" %
                                        token.start)
                    if indent_level > level:
                        for l in range(indent_level - level):
                            yield Token("INDENT", indent_with)
                    elif indent_level < level:
                        for l in range(level - indent_level):
                            yield Token("DEDENT", '')
                    level = indent_level
                else:
                    for l in range(level):
                        yield Token("DEDENT", '')
                    level = 0
                    yield token
            elif token.type != "SPACE":
                yield token
    for l in range(level):
        yield Token("DEDENT", '')


tokval = lambda tok: tok.value
const = lambda s: a(Token("NAME", s)) >> tokval
t = lambda tp: lambda x: x.type == tp
op = lambda s: a(Token("OP", s)) >> tokval

anno = lambda tp: lambda x: (tp, x)
append = lambda head_tail: head_tail[0] + [head_tail[1]] \
    if head_tail[1] else head_tail[0]
always = lambda val: lambda _: val
strip = lambda char: lambda x: x.strip(char)


def list2dict(key_optional_vals):
    required = []
    kvs = {}
    definitions = {}
    sealed = True
    refid = None
    ref_declaration = {}
    for (key, optional, val) in key_optional_vals:
        if key == "@":
            definitions[optional] = val
        elif optional == "open":
            sealed = False
        elif optional == "id":
            refid = val
        elif optional == "extref":
            ref_declaration[key] = val
        else:
            if not optional:
                required.append(key)
            kvs[key] = val
    return (kvs, required, sealed, definitions, refid, ref_declaration)


def parse(tokens):
    name = some(t('NAME')) >> tokval

    raw_string = some(t('STRING')) >> tokval >> strip('"')

    num = some(t('NUMBER')) >> tokval >> float
    true = const('true') >> always(True)
    false = const('false') >> always(False)
    null_ = const('null') >> always(None)

    enum_item = (num | true | false | null_ | name | raw_string)
    enum = many(enum_item + skip(op("|"))) + enum_item >> append \
        >> anno("enum")

    boolean = const("bool") >> always(None) >> anno("boolean")
    null = const("null") >> always(None) >> anno("null")

    num_range = skip(op('{')) + maybe(num) + \
        skip(op(",")) + maybe(num) + skip(op('}')) >> tuple

    regexp = some(t("REGEXP")) >> tokval >> strip("/")
    string = ((skip(const("str")) +
               maybe(num_range) + maybe(regexp)) |
              (maybe(num_range) + (regexp))) \
        >> anno("string")

    _format = skip(op("%")) + name >> anno("format")

    num_range_step = skip(op('{')) + maybe(num) + \
        skip(op(",")) + maybe(num) + \
        maybe(skip(op(",")) + num) + skip(op('}')) >> tuple

    number = skip(const("num")) + maybe(num_range_step) >> anno("number")
    integer = skip(const("int")) + maybe(num_range_step) >> anno("integer")

    schema = forward_decl()

    array = skip(op('[')) \
        + (many(schema + skip(op(","))) + maybe(schema) >> append) \
        + skip(op(']')) + maybe(num_range) + maybe(op("!")) >> anno("array")

    indent = some(t("INDENT")) >> tokval >> anno("indent")
    dedent = some(t("DEDENT")) >> tokval
    nl = some(t('NL'))
    definition = op("@") + name
    key = (((name | string) + maybe(op("?"))) | definition) + skip(op(":"))

    ref = skip(op("@")) + (name | name + skip(op(":")) + name) >> anno("ref")
    ref_declaration = skip(op("@")) + name + raw_string \
        >> (lambda name_url: (name_url[0], "extref", name_url[1]))

    base_schema = ref | string | number | integer | boolean | null | _format \
        | array

    oneof = oneplus(base_schema + skip(op("|"))) + base_schema \
        >> append >> anno("oneof")
    anyof = oneplus(base_schema + skip(op("/"))) + base_schema \
        >> append >> anno("anyof")
    allof = oneplus(base_schema + skip(op("&"))) + base_schema \
        >> append >> anno("allof")
    simple_schema = anyof | oneof | allof | base_schema | enum | array

    dots = op("...") >> always((None, "open", None))
    refid = skip(op("@")) + raw_string >> (lambda x: (None, "id", x))

    obj = forward_decl()
    nested_obj = skip(nl) + skip(indent) + obj + skip(dedent)
    obj.define(oneplus(((key + ((simple_schema + skip(nl)) | nested_obj))
                       | ((dots | refid | ref_declaration) + skip(nl)))
                       >> list) >> list2dict >> anno("object"))

    schema.define(obj | simple_schema)

    exprs = skip(maybe(nl)) + schema + skip(maybe(nl)) + skip(finished)
    return exprs.parse(list(tokens))


def generate_schema(node):
    (tp, val) = node
    if tp == "enum":
        return {"enum": val}
    elif tp == "string":
        (nrange, pattern) = val
        ret = {"type": tp}
        if nrange is not None:
            (nmin, nmax) = nrange
            if nmin is not None:
                ret["minLength"] = nmin
            if nmax is not None:
                ret["maxLength"] = nmax
        if pattern is not None:
            ret["pattern"] = pattern
        return ret
    elif tp == "number" or tp == "integer":
        ret = {"type": tp}
        if val is not None:
            (l, h, step) = val
            if l is not None:
                ret["minimum"] = l
            if h is not None:
                ret["maximum"] = h
            if step is not None:
                ret["multipleOf"] = step
        return ret
    elif tp == "ref":
        return {"$ref": "#/definitions/%s" % val}
    elif tp == "array":
        ret = {"type": tp}
        (items, size_range, unique) = val
        if items:
            if (len(items)) == 1:
                ret["items"] = generate_schema(items[0])
            else:
                ret["items"] = list(map(generate_schema, items))
        if size_range:
            (l, h) = size_range
            if h is not None:
                ret["maxItems"] = h
            if l is not None:
                ret["minItems"] = l
        if unique:
            ret["uniqueItems"] = True
        return ret
    elif tp == "object":
        properties = {}
        (kvs, required, sealed, definitions, refid, ref_declarations) = val
        for (k, v) in kvs.items():
            properties[k] = generate_schema(v)
        ret = {"type": "object", "properties": properties}
        if required:
            ret["required"] = required
        if sealed:
            ret["additionalProperties"] = False
        if refid:
            ret["id"] = refid
        if definitions:
            defs = {}
            for (k, v) in definitions.items():
                defs[k] = generate_schema(v)
            ret["definitions"] = defs
        return ret
    elif tp == "anyof" or tp == "oneof" or tp == "allof":
        return dict([(tp[:3] + "Of", list(map(generate_schema, val)))])
    elif tp == "format":
        return {"format": val}
    elif tp == "boolean":
        return {"type": "boolean"}
    elif tp == "null":
        return {"type": "null"}


def loads(source):
    """example input
@role: admin | author | collaborator | role with space

@user:
    name: str{3,20}
    age: int{10,200}
    gender: male | female
    roles: [@role]
    description?: str{,200}
"""
    return generate_schema(parse(tokenize(source)))


def load(fp):
    return loads(fp.read())
