import typing as t
from functools import wraps

from flask import request

from azure_oidc import OIDCConfig
from azure_oidc.auth import AzureADAuth


class HTTPUnauthorized(Exception):
    def __init__(self, *, description: str):
        self.description = description


class FlaskOIDCAuthDecorator:
    def __init__(self, oidc_config: OIDCConfig):
        self._authenticator = AzureADAuth(oidc_config)

    def __call__(self, *, auth_scopes: t.Union[str, t.Tuple[()], t.Tuple[str]] = ()):
        def decorator(view_func: t.Callable) -> t.Callable:
            @wraps(view_func)
            def wrapper(*args, **kwargs):
                try:
                    auth_header = request.headers["AUTHORIZATION"]
                except KeyError as ex:
                    raise HTTPUnauthorized(description="Authorization header is required but was not provided") from ex

                nonlocal auth_scopes
                if isinstance(auth_scopes, str):
                    auth_scopes = (auth_scopes,)

                try:
                    self._authenticator.authenticate(auth_header, auth_scopes=auth_scopes)
                except AzureADAuth.AuthError as ex:
                    raise HTTPUnauthorized(description=ex.args[0]) from ex

                return view_func(*args, **kwargs)

            return wrapper

        return decorator
