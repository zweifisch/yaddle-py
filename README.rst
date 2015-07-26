yaddle
======

|Build Status|

Yet Another Data format Description LanguagE

::

    @role: admin | author | collaborator | "role with space"

    user:
      name: str{3,20}
      age: int{10,200}
      gender: male | female
      roles: [@role]
      description?: str{,200}

translated to json-schema

.. code:: javascript

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

api
---

use load/loads to translate yaddle into json-schema

.. code:: py

    from yaddle import load, loads
    load(open("some.ydl"))
    loads("""[str]{,3}""")

cli

.. code:: sh

    cat schema.ydl | python -m yaddle.tool

more details
------------

number
~~~~~~

::

    int{100,200}

.. code:: javascript

    {
        "type": "integer",
        "minimum": 100,
        "maximum": 200
    }

::

    num{,,0.1}

.. code:: javascript

    {
        "type": "number",
        "multipleOf": 0.1
    }

string
~~~~~~

::

    str{1,2} /pattern/

.. code:: javascript

    {
        "type": "string",
        "minLength": 1,
        "maxLength": 20,
        "pattern": "pattern"
    }

::

    /pattern/

.. code:: javascript

    {
        "type": "string",
        "pattern": "pattern"
    }

format ``date-time``, ``email``, ``hostname``, ``ipv4``, ``ipv6``,
``uri``

::

    %email

.. code:: javascript

    {
        "format": "email"
    }

array
~~~~~

::

    [str]{1,10}

.. code:: javascript

    {
        "type": "array",
        "minItems": 1,
        "maxItems": 10,
        "items": {
            "type": "string"
        }
    }

::

    [str|num]

.. code:: javascript

    {
        "type": "array",
        "items": {
            oneOf: [
                {"type": "string"},
                {"type": "number"}
            ]
        }
    }

::

    [str, num]

.. code:: javascript

    {
        "type": "array",
        "items": [
            {"type": "string"},
            {"type": "number"}
        }
    }

``!`` for uniqueItems

::

    [num]!

.. code:: javascript

    {
        "type": "array",
        "items": {
            {type: "number"}
        },
        "uniqueItems": true
    }

object
~~~~~~

-  all properties are required, except those one with a ``?`` suffix
-  ``...`` to allow ``additionalProperties``

::

    key: str
    size?: number
    ...

.. code:: javascript

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

oneOf, anyOf, allOf
~~~~~~~~~~~~~~~~~~~

-  ``|`` for oneOf like ``@ref | @ref2``
-  ``/`` for anyOf
-  ``&`` for allOf

reference
~~~~~~~~~

local reference

::

    @address:
        street_address: str
        city: str
        state: str

    billing_address: @address
    shipping_address: @address

.. code:: javascript

    {
      "additionalProperties": false,
      "definitions": {
        "address": {
          "additionalProperties": false,
          "required": [
            "street_address",
            "city",
            "state"
          ],
          "type": "object",
          "properties": {
            "city": {
              "type": "string"
            },
            "state": {
              "type": "string"
            },
            "street_address": {
              "type": "string"
            }
          }
        }
      },
      "required": [
        "billing_address",
        "shipping_address"
      ],
      "type": "object",
      "properties": {
        "billing_address": {
          "$ref": "#/definitions/address"
        },
        "shipping_address": {
          "$ref": "#/definitions/address"
        }
      }
    }

referece remote schema(TBD)

::

    @"http://example.com/schema"

    @product:
        price: num{0,}
        title: str{,200}

referece it in another schema

::

    @example: "http://example.com/schema"

    products: [@example:product]

examples
--------

example from http://json-schema.org/example2.html translated to yaddle

::

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

.. |Build Status| image:: https://img.shields.io/travis/zweifisch/yaddle-py.svg?style=flat
   :target: https://travis-ci.org/zweifisch/yaddle-py
