#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
import re
from jsonschema import Draft4Validator
from jsonschema import ValidationError  # noqa


class JsonSchemaValidator(Draft4Validator):
    def __init__(self, schema, *args, **kwargs):
        super(JsonSchemaValidator, self).__init__(schema, *args, **kwargs)


JsonValidationError = ValidationError


OBJECTID_SCHEMA = {
    'type': 'string',
    'pattern': re.compile(r'^[0-9a-fA-F]{24}(?!.)'),
}

OBJECTID_OR_EMPTY_SCHEMA = {
    'oneOf': [
        {
            'type': 'string',
            'pattern': re.compile(r'^[0-9a-fA-F]{24}(?!.)'),
        },
        {
            'type': 'string',
            'enum': [''],
        },
    ],
}

TIME_SCHEMA = {
    'type': 'integer',
    'maximum': int(time.time()) * 10,  # 防止 js 传入毫秒记的时间
    'minimum': 0,
}

INT_SCHEMA = {
    'type': 'integer',
}

NUMBER_SCHEMA = {
    'type': 'number',
}

STRING_SCHEMA = {
    'type': 'string',
}

ARRAY_STRING_SCHEMA = {
    'type': 'array',
    'items': STRING_SCHEMA,
}

ARRAY_INT_SCHEMA = {
    'type': 'array',
    'items': INT_SCHEMA,
}

MD5_SCHEMA = {
    'type': 'string',
    'pattern': r'^[0-9a-fA-F]{32}$',
}

MD5_OR_EMPTY_SCHEMA = {
    'oneOf': [
        MD5_SCHEMA,
        {
            'type': 'string',
            'enum': [''],
        }
    ],
}

CURSOR_SCHEMA = {
    'type': 'string',
}

BOOL_SCHEMA = {
    'type': 'boolean'
}
