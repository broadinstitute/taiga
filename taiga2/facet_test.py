from taiga2 import facet

def test_single_enum_validation():
    e = facet.Enum(values = [
                facet.EnumValue("user", "User"),
                facet.EnumValue("admin", "Admin") 
                ])

    assert e.is_value_valid("user")
    assert e.is_value_valid("admin")
    assert not e.is_value_valid("invalid")
    assert not e.is_value_valid(["admin"])
    assert not e.is_value_valid(1)
    assert not e.is_value_valid(dict())

def test_multi_enum_validation():
    e = facet.Enum(values = [
                facet.EnumValue("user", "User"),
                facet.EnumValue("admin", "Admin") 
                ], is_collection=True)

    assert e.is_value_valid(["user"])
    assert e.is_value_valid(["admin"])
    assert e.is_value_valid(["admin", "user"])
    assert e.is_value_valid(["user", "admin"])
    assert not e.is_value_valid("user")
    assert not e.is_value_valid(dict())

def test_basic_def_validation():
    user_def = facet.FacetDef(properties = [
        facet.Property(name = "name",
            required = True,
            type = facet.String()),

        facet.Property(name = "access",
            required = True,
            type = facet.Enum(values = [
                facet.EnumValue("user", "user"),
                facet.EnumValue("admin", "admin"),
            ])),
        
        facet.Property(name = "email",
            required = False,
            type = facet.String()),
        ])

    assert user_def.is_valid(dict(name="joe", access="user", email="foo@sample.com"))
    assert user_def.is_valid(dict(name="joe", access="user"))
    assert user_def.is_valid(dict(name="joe", access="user", other="misc"))
    
    assert not user_def.is_valid(dict(name=[], access="user"))
    assert not user_def.is_valid(dict(name="joe", access="invalid"))
    assert not user_def.is_valid(dict(name="joe", access=2))
