# PENDING

  * **BREAKING** Dropped Python2 Support
  * **BREAKING** Modified behavior of `default` field property
    to only set a default if `output_missing` is true.
  * Fixed schema reference issue with `Any` fields
  * Fixed SelfReference field issue with Polymorphic parents
  * Fixed sub schema values not respecting name key
  * Fixed sub schema default values not setting correctly
  * Fixed issue with None values not applying defaults
  * Fixed sub schema unnecessarily outputting when missing
  * Fixed sub schema default value not respecting name key
  * Fixed sub schema mishandling load/name
  * Fixed parent schema mishandling load/name
  * Fixed inability to set same load key on multiple fields
  * Fixed child element errors for sub-object data
  * Fixed child field value invaid caching
  * Modularization updates
  * Added repr and str to exceptions
  * Fixed issue with None being default-allowed in subschemas, updated tests
  * Added benchmark test
  * Fixed serialize callable for name change


# 0.6.0

  * Schema `validate()`, `deserialize()`, `serialize()` and `encode()`
    now make use of whitelist, blacklist, tags, and context. fixes issue #2
  * Added updated `validation()` method to PolySchema. fixes issue #3
  * Added `load` kwarg to Fields. Declares the key to lookup when deserializing *only*
  * Added `Child` field type -- Allows the use of nested values
  * Added `Any` field type -- Allows a "one of X fields" field
  * Added `Anything` field type -- Passthrough field type
  * fixed issue with PolySchema not getting it's own poly mapping instance
  * fixed issue with `name` not being respected on some missing values
  * `post_*` schema callables are now called even if no
     value was set.
  * `pre_validate` and `post_validate` schema callables are now
     called during `validate()`.
  * `fields.Schema` now correctly passes validation options
  * `fields.Schema` now tracks field level options
  * `fields.Schema` can now serialize polymorphic schemas
  * `fields.Schema` now deserializes as objects
  * `output_missing` no longer assumes `allow_none` behavior
  * `output_missing` now also checks against field level options
  * `allow_none` is now respected with required fields


# 0.2.1

  * initial Ciri package
