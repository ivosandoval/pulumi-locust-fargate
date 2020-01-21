import base64
import hashlib
import json

import pulumi
config = pulumi.Config()


def sha256sum(filename):
    """
    Helper function that calculates the hash of a file
    using the SHA256 algorithm

    Inspiration:
    https://stackoverflow.com/a/44873382

    NB: we're deliberately using `digest` instead of `hexdigest` in order to mimic Terraform
    """
    h  = hashlib.sha256()
    b  = bytearray(128*1024)
    mv = memoryview(b)
    with open(filename, 'rb', buffering=0) as f:
        for n in iter(lambda : f.readinto(mv), 0):
            h.update(mv[:n])
    return h.digest()

def filebase64sha256(filename):
    """
    Computes the Base64-encoded SHA256 hash of a file
    """
    h = sha256sum(filename)
    b = base64.b64encode(h)
    return b.decode()

def format_resource_name(name):
    """
    Defines a fully-formated resource name
    """
    template = '{project}-{stack}-{name}'
    resource_name = template.format(
        name=name,
        project=pulumi.get_project(),
        stack=pulumi.get_stack(),
    )
    return resource_name

def json_as_string_from_file(path):
    """
    Return a string json from json file
    """
    with open(path) as f:
        json_data=json.load(f)
        data_str=json.dumps(json_data)
        return data_str