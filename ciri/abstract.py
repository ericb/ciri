from abc import ABCMeta

# Type Definitions
AbstractField = type('AbstractField', (object,), {})
AbstractSchema = type('AbstractSchema', (object,), {})
AbstractPolySchema = type('AbstractPolySchema', (AbstractSchema,), {})
SchemaFieldDefault = type('SchemaFieldDefault', (object,), {})
SchemaFieldMissing = type('SchemaFieldMissing', (object,), {})
UseSchemaOption = type('UseSchemaOption', (object,), {})
