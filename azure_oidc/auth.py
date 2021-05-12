import logging
import typing as t
from functools import lru_cache

from .config import OIDCConfig
from .jwt_validation import OIDCBearerTokenValidator


@lru_cache(maxsize=None)
def _get_validator(config: OIDCConfig) -> OIDCBearerTokenValidator:
    return OIDCBearerTokenValidator(config)


class AzureADAuth:
    class AuthError(Exception):
        pass

    def __init__(self, oidc_config: OIDCConfig):
        self._validator = _get_validator(oidc_config)

        if _get_validator.cache_info().currsize > 1:
            logging.getLogger("azure AD auth").warning(
                "_get_validator cache size > 1; avoid creating more than one instance "
                "of OIDCConfig in your application to reduce calls to the Azure JWKs "
                "endpoint"
            )

    def authenticate(self, auth_header: str, *, auth_scopes: t.Iterable[str] = []):
        try:
            auth_type, token = auth_header.split()
        except ValueError as ex:
            raise AzureADAuth.AuthError(
                "Authorization header must have two parts separated by whitespace"
            ) from ex

        if auth_type.lower() != "bearer":
            raise AzureADAuth.AuthError('Authorization header must begin with "Bearer"')

        try:
            claims = self._validator.validate_bearer_token(token)
        except self._validator.ValidationError as ex:
            raise AzureADAuth.AuthError("JWT failed validation") from ex

        if auth_scopes:
            claimed_scopes = claims["scp"].split()
            missing_scopes = [
                scope for scope in auth_scopes if scope not in claimed_scopes
            ]
            if missing_scopes:
                raise AzureADAuth.AuthError(
                    "Not all required scopes are present. "
                    f"Expected {','.join(auth_scopes)}, got {', '.join(claimed_scopes)}"
                )
