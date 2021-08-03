import typing as t

import falcon

from azure_oidc.auth import AzureADAuth
from azure_oidc.config import OIDCConfig


class FalconOIDCAuthMiddleware:
    def __init__(self, oidc_config: OIDCConfig):
        self._authenticator = AzureADAuth(oidc_config)

    def process_resource(self, req: falcon.Request, resp: falcon.Response, resource: object, params: dict) -> None:
        # allow disabling auth on a resource with `auth_disable = True`
        if getattr(resource, "auth_disable", False) is True:
            return

        try:
            auth_header = req.headers["AUTHORIZATION"]
        except KeyError as ex:
            raise falcon.HTTPUnauthorized(description="Authorization header is required but was not provided") from ex

        auth_scopes: t.Iterable = getattr(resource, "auth_scopes", ())
        if isinstance(auth_scopes, str):
            auth_scopes = (auth_scopes,)

        try:
            self._authenticator.authenticate(auth_header, auth_scopes=auth_scopes)
        except AzureADAuth.AuthError as ex:
            raise falcon.HTTPUnauthorized(description=ex.args[0]) from ex
