import re


class ContainsAnyDict(dict):
    """
    Accept frontend-created optional inputs whose names are not known in Python.

    The JavaScript extension creates widgets named uri_1, uri_2, ...
    ComfyUI checks optional inputs against this mapping before passing them to
    the node function, so every key must be treated as a valid multiline string.
    """

    def __contains__(self, key):
        return True

    def __getitem__(self, key):
        return ("STRING", {"multiline": True})

    def get(self, key, default=None):
        return self[key]


def uri_sort_key(key: str):
    match = re.match(r"^uri_(\d+)$", key)
    return (0, int(match.group(1))) if match else (1, key)


def collect_uri_list(kwargs) -> list[str]:
    uri_list = []
    for key in sorted(kwargs, key=uri_sort_key):
        if not key.startswith("uri_"):
            continue
        uri = kwargs[key]
        if not isinstance(uri, str):
            continue
        uri = uri.strip()
        if uri:
            uri_list.append(uri)
    return uri_list
