def json_default(json: dict[str, any], key: str, default):
    return json[key] if key in json and json[key] != None else default


def attribute_exists(json: dict[str, any], key: str):
    return key in json and json[key] != None
