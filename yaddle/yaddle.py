from funcparserlib.parser import (some, a, many, skip, finished, maybe,
                                  forward_decl, oneplus)
from funcparserlib.lexer import make_tokenizer, Token


def tokenize(input):
    token_specs = [
        ('NAME', (r'[A-Za-z_][A-Za-z_0-9]*',)),
        ('OP', (r'([{}\[\]?$:,|@]|\.{3})',)),
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
flatten = lambda l: sum(([x] if not isinstance(x, (list, tuple))
                        else flatten(x) for x in l), [])
anno = lambda tp: lambda x: (tp, x)
append = lambda (head, tail): head + [tail] if tail else head
fst = lambda (xs): xs[0]
always = lambda val: lambda _: val


def list2dict(key_optional_vals):
    required = []
    kvs = {}
    definations = {}
    sealed = True
    for (key, optional, val) in key_optional_vals:
        if key is None:
            sealed = False
        elif key == "@":
            definations[optional] = val
        else:
            if not optional:
                required.append(key)
            kvs[key] = val
    return (kvs, required, sealed, definations)


def num2int(num_range):
    if num_range is None:
        return (None, None, 1)
    (f, s) = num_range
    return (f, s, 1)


def parse(tokens):
    name = some(t('NAME')) >> tokval
    space = some(t('SPACE')) >> tokval
    name_with_space = name + many(space + name) >> flatten >> join

    pipe = op('|')
    ospace = skip(maybe(space))
    enum = name_with_space + \
        oneplus(ospace + skip(pipe) + ospace + name_with_space) \
        >> flatten >> anno("enum")

    num = some(t('NUMBER')) >> tokval >> int
    num_range = skip(op('{')) + ospace + maybe(num) + ospace + \
        skip(op(",")) + ospace + maybe(num) + \
        ospace + skip(op('}')) >> tuple

    regexp = some(t("REGEXP")) >> tokval >> (lambda x: x.strip("/"))
    string = ((skip(const("str")) +
               maybe(num_range) + ospace + maybe(regexp)) |
              (maybe(num_range) + ospace + (regexp))) \
        >> anno("string")

    num_range_step = skip(op('{')) + ospace + maybe(num) + ospace + \
        skip(op(",")) + ospace + maybe(num) + \
        maybe(skip(op(",")) + ospace + num) + \
        ospace + skip(op('}')) >> tuple

    number = skip(const("num")) + maybe(num_range_step) >> anno("number")
    integer = skip(const("int")) + maybe(num_range) \
        >> num2int >> anno("number")

    schema = forward_decl()
    array = skip(op('[')) \
        + (many(schema + ospace + skip(op("|"))) + ospace + maybe(schema) >> append) \
        + skip(op(']')) + maybe(num_range) >> anno("array")

    indent = some(t("INDENT")) >> tokval >> anno("indent")
    dedent = some(t("DEDENT")) >> tokval
    nl = some(t('NL'))
    defination = op("@") + name
    key = ((name_with_space + maybe(op("?"))) | defination) \
        + ospace + skip(op(":")) + ospace
    dots = op("...") >> always((None, None, None))

    ref = skip(op("@")) + name >> anno("ref")

    obj = forward_decl()
    oneline_schema = (ref | string | number | integer | enum | array)
    nested_obj = skip(nl) + skip(indent) + obj + skip(dedent)
    obj.define(oneplus(((key + ((oneline_schema + skip(nl)) | nested_obj))
                       | (dots + skip(nl)))
                       >> list) >> list2dict >> anno("object"))

    schema.define(obj | oneline_schema)

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
    elif tp == "number":
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
        return {"$ref": "#/definations/%s" % val}
    elif tp == "array":
        ret = {"type": tp}
        (items, size_range) = val
        items = list(map(generate_schema, items))
        if items:
            if len(items) > 1:
                ret["items"] = {"anyOf": items}
            else:
                ret["items"] = items[0]
        if size_range:
            (l, h) = size_range
            if h is not None:
                ret["maxItems"] = h
            if l is not None:
                ret["minItems"] = l
        return ret
    elif tp == "object":
        properties = {}
        (kvs, required, sealed, definations) = val
        for (k, v) in kvs.items():
            properties[k] = generate_schema(v)
        ret = {"type": "object", "properties": properties,
               "required": required, "additionalProperties": not sealed}
        if definations:
            defs = {}
            for (k, v) in definations.items():
                defs[k] = generate_schema(v)
            ret["definations"] = defs
        return ret


def loads(source):
    """example input
@role: admin | author | collaborator | role with space

@user:
    name: str{3,20}
    age: int{10,200}
    gender: male | female
    roles: [@role]
    description?: str{200}
"""
    return generate_schema(parse(tokenize(source)))
