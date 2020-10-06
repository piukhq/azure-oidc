import typing as t


class OIDCConfig(t.NamedTuple):
    base_url: str
    issuer: str
    audience: str
