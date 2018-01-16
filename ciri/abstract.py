from abc import ABCMeta

# Type Definitions
AbstractField = type('AbstractSchema', (object,), {})
AbstractSchema = type('AbstractSchema', (object,), {})
SchemaFieldDefault = type('SchemaFieldDefault', (object,), {})
SchemaFieldMissing = type('SchemaFieldMissing', (object,), {})
UseSchemaOption = type('SchemaFieldMissing', (object,), {})
