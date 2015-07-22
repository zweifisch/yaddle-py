from funcparserlib.parser import (some, a, many, skip, finished, maybe,
                                  forward_decl, oneplus)
from funcparserlib.lexer import make_tokenizer, Token


def tokenize(input):
    token_specs = [
        ('NAME', (r'[A-Za-z_][A-Za-z_0-9-]*',)),
        ('OP', (r'([{}\[\]?$:,|@%!]|\.{3})',)),
        ('REGEXP', (r'/.*/',)),
        ('NUMBER', (r'0|([1-9][0-9]*)',)),
        ('COMMENT', (r'#.*',)),
        ('NL', (r'\n+',)),
        ('SPACE', (r'[ \t]+',))
    ]
    t = make_tokenizer(token_specs)
    return indentation(t("\n".join([l.rstrip() for l in input.splitlines()])))


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
            else:
                yield token
    yield Token("NL", "\n")  # make last line looks the same as other lines
    for l in range(level):
        yield Token("DEDENT", '')


tokval = lambda tok: tok.value
const = lambda s: a(Token("NAME", s)) >> tokval
t = lambda tp: lambda x: x.type == tp
op = lambda s: a(Token("OP", s)) >> tokval

join = lambda x: "".join(x)
anno = lambda tp: lambda x: (tp, x)
append = lambda (head, tail): head + [tail] if tail else head
prepend = lambda (first, rest): [first] + rest
fst = lambda (xs): xs[0]
always = lambda val: lambda _: val


def list2dict(key_optional_vals):
    required = []
    kvs = {}
    definitions = {}
    sealed = True
    for (key, optional, val) in key_optional_vals:
        if key is None:
            sealed = False
        elif key == "@":
            definitions[optional] = val
        else:
            if not optional:
                required.append(key)
            kvs[key] = val
    return (kvs, required, sealed, definitions)


def parse(tokens):
    name = some(t('NAME')) >> tokval
    space = some(t('SPACE')) >> tokval
    # cant use append here
    name_with_space = name + many(space + name >> join) >> prepend >> join

    ospace = skip(maybe(space))
    enum = many(name_with_space + ospace + skip(op("|")) + ospace) \
        + name_with_space >> append >> anno("enum")

    boolean = const("bool") >> always(None) >> anno("boolean")
    null = const("null") >> always(None) >> anno("null")

    num = some(t('NUMBER')) >> tokval >> int
    num_range = skip(op('{')) + ospace + maybe(num) + ospace + \
        skip(op(",")) + ospace + maybe(num) + \
        ospace + skip(op('}')) >> tuple

    regexp = some(t("REGEXP")) >> tokval >> (lambda x: x.strip("/"))
    string = ((skip(const("str")) +
               maybe(num_range) + ospace + maybe(regexp)) |
              (maybe(num_range) + ospace + (regexp))) \
        >> anno("string")

    _format = skip(op("%")) + name >> anno("format")

    num_range_step = skip(op('{')) + ospace + maybe(num) + ospace + \
        skip(op(",")) + ospace + maybe(num) + \
        maybe(skip(op(",")) + ospace + num) + \
        ospace + skip(op('}')) >> tuple

    number = skip(const("num")) + maybe(num_range_step) >> anno("number")
    integer = skip(const("int")) + maybe(num_range_step) >> anno("integer")

    schema = forward_decl()
    array = skip(op('[')) + maybe(schema) + skip(op(']')) + maybe(num_range) \
        + maybe(op("!")) >> anno("array")

    indent = some(t("INDENT")) >> tokval >> anno("indent")
    dedent = some(t("DEDENT")) >> tokval
    nl = some(t('NL'))
    definition = op("@") + name
    key = ((name_with_space + maybe(op("?"))) | definition) \
        + ospace + skip(op(":")) + ospace
    dots = op("...") >> always((None, None, None))

    ref = skip(op("@")) + name >> anno("ref")

    base_schema = ref | string | number | integer | boolean | null | _format \
        | array

    oneof = oneplus(base_schema + ospace + skip(op("|")) + ospace) + base_schema \
        >> append >> anno("oneof")
    anyof = oneplus(base_schema + ospace + skip(op(",")) + ospace) + base_schema \
        >> append >> anno("anyof")
    allof = oneplus(base_schema + ospace + skip(op("&")) + ospace) + base_schema \
        >> append >> anno("allof")
    simple_schema = anyof | oneof | allof | base_schema | enum | array

    obj = forward_decl()
    nested_obj = skip(nl) + skip(indent) + obj + skip(dedent)
    obj.define(oneplus(((key + ((simple_schema + skip(nl)) | nested_obj))
                       | (dots + skip(nl)))
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
        (schema, size_range, unique) = val
        if schema:
            ret["items"] = generate_schema(schema)
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
        (kvs, required, sealed, definitions) = val
        for (k, v) in kvs.items():
            properties[k] = generate_schema(v)
        ret = {"type": "object", "properties": properties,
               "required": required}
        if sealed:
            ret["additionalProperties"] = False
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
