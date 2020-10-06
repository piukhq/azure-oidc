import json
import logging

import requests
from jwcrypto.jwk import JWKSet
from jwcrypto.jwt import JWT

from .config import OIDCConfig


class OIDCBearerTokenValidator:
    class ValidationError(Exception):
        pass

    def __init__(self, config: OIDCConfig) -> None:
        self.log = logging.getLogger("oidc-bearer-validator")
        self._config = config
        self._metadata = self._download_metadata()
        self._jwks = self._download_jwks()

    @property
    def _metadata_uri(self) -> str:
        return f"{self._config.base_url}/.well-known/openid-configuration"

    @property
    def _jwks_uri(self) -> str:
        return self._metadata["jwks_uri"]

    def _download_metadata(self) -> dict:
        self.log.info(f"Downloading OIDC metadata from {self._metadata_uri}")
        resp = requests.get(self._metadata_uri)
        resp.raise_for_status()
        return resp.json()

    def _download_jwks(self) -> dict:
        self.log.info(f"Downloading JWKs from {self._jwks_uri}")
        resp = requests.get(self._jwks_uri)
        resp.raise_for_status()
        jwks = JWKSet.from_json(resp.text)
        self.log.info(f"Downloaded {len(jwks['keys'])} JWKs from {self._jwks_uri}")
        return jwks

    def validate_bearer_token(self, token: str) -> dict:
        try:
            jwt = JWT(
                jwt=token, key=self._jwks, check_claims={"aud": self._config.audience, "iss": self._config.issuer}
            )
        except Exception as ex:
            raise self.ValidationError from ex

        return json.loads(jwt.claims)
