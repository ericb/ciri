# PENDING

  * Schema `validate()`, `deserialize()`, `serialize()` and `encode()`
    now make use of whitelist, blacklist, tags, and context. fixes issue #2
  * Added updated `validation()` method to PolySchema. fixes issue #3
  * Added `load` kwarg to Fields. Declares the key to lookup.
  * Added `Child` field type -- Allows the use of nested values
  * fixed issue with PolySchema not getting it's own poly mapping instance
  * fixed issue with `name` not being respected on some missing values
  * `post_*` schema callables are now called even if no
     value was set.
  * `pre_validate` and `post_validate` schema callables are now
     called during `validate()`. 
  * `fields.Schema` now correctly passes validation options
  * `fields.Schema` now tracks field level options
  * `fields.Schema` can now serialize polymorphic schemas 
  * `output_missing` no longer assumes `allow_none` behavior
  * `output_missing` now also checks against field level options


# 0.2.1

  * initial Ciri package
