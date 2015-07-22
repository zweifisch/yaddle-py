# yaddle

Yet Another Data format Description LanguagE

```yaml
@role: admin | author | collaborator | "role with space"

user:
  name: str{3,20}
  age: int{10,200}
  gender: male | female
  roles: [@role]
  description?: str{,200}
```

translated to json-schema
```javascript
{
  "additionalProperties": false,
  "definitions": {
    "role": {
      "enum": [
        "admin",
        "author",
        "collaborator",
        "role with space"
      ]
    }
  },
  "required": [
    "user"
  ],
  "type": "object",
  "properties": {
    "user": {
      "additionalProperties": false,
      "required": [
        "name",
        "age",
        "gender",
        "roles"
      ],
      "type": "object",
      "properties": {
        "gender": {
          "enum": [
            "male",
            "female"
          ]
        },
        "age": {
          "minimum": 10,
          "type": "integer",
          "maximum": 200
        },
        "name": {
          "minLength": 3,
          "type": "string",
          "maxLength": 20
        },
        "roles": {
          "items": {
            "$ref": "#/definitions/role"
          },
          "type": "array"
        },
        "description": {
          "type": "string",
          "maxLength": 200
        }
      }
    }
  }
}
```

## api

use load/loads to translate yaddle into json-schema

```py
from yaddle import load, loads
load("some.ydl")
loads("""[str]{,3}""")
```

## more details

### number

```
int{100,200}
```

```javascript
{
    "type": "integer",
    "minimum": 100,
    "maximum": 200
}
```

```
num{,,0.1}
```

```javascript
{
    "type": "number",
    "multipleOf": 0.1
}
```

### string

```
str{1,2} /pattern/
```

```javascript
{
    "type": "string",
    "minLength": 1,
    "maxLength": 20,
    "pattern": "pattern"
}
```

```
/pattern/
```

```javascript
{
    "type": "string",
    "pattern": "pattern"
}
```

format `date-time`, `email`, `hostname`, `ipv4`, `ipv6`, `uri`

```
%email
```

```javascript
{
    "format": "email"
}
```

### array

```
[str]{1,10}
```

```javascript
{
    "type": "array",
    "minItems": 1,
    "maxItems": 10,
    "items": {
        "type": "string"
    }
}
```

```
[str|num]
```

```javascript
{
    "type": "array",
    "items": {
        oneOf: [
            {"type": "string"},
            {"type": "number"}
        ]
    }
}
```

```
[str, num]
```

```javascript
{
    "type": "array",
    "items": [
        {"type": "string"},
        {"type": "number"}
    }
}
```

`!` for uniqueItems

```
[num]!
```

```javascript
{
    "type": "array",
    "items": {
        {type: "number"}
    },
    "uniqueItems": true
}
```

### object

- all properties are required, except those one with a `?` suffix
- `...` to allow `additionalProperties`

```
key: str
size?: number
...
```

```javascript
{
    "type": "object",
    "properties": {
        "key": {
            "type": "string"
        },
        "size": {
            "type": "number"
        },
        "required": ["key"]
    }
    "additionalProperties": true
}
```

## examples

example from http://json-schema.org/example2.html translated to yaddle

```
@diskDevice:
    type: disk
    divice: /^/dev/[^/]+(/[^/]+)*$/
@diskUUID:
    type: disk
    label: /^[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}$/
@nfs:
    type: nfs
    remotePath: /^(/[^/]+)+$/
    server: %host-name | %ipv4 | %ipv6
@tmpfs:
    type: tmpfs
    sizeInMB: int{16,512}

storage: @diskDevice | @diskUUID | @nfs | @tmpfs
fstype?: ext3 | ext4 | btrfs
options?: [str]{1,}!
readonly?: bool
```
