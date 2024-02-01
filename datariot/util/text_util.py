def create_uuid_from_string(val: str):
    import uuid
    import hashlib
    hex_string = hashlib.md5(val.encode("UTF-8")).hexdigest()
    return str(uuid.UUID(hex=hex_string))