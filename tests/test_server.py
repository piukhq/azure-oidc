import logging
import typing as t
from enum import Enum

from azure_oidc import OIDCConfig

import click

LOG_FORMAT = "%(asctime)s | %(levelname)8s | %(name)s\n%(message)s"
logging.basicConfig(format=LOG_FORMAT, level=logging.DEBUG)

tenant_id = "a6e2367a-92ea-4e5a-b565-723830bcc095"
config = OIDCConfig(
    base_url=f"https://login.microsoftonline.com/{tenant_id}/v2.0",
    issuer=f"https://sts.windows.net/{tenant_id}/",
    audience="api://bink.harmonia",
)


def create_falcon_app() -> t.Any:
    import falcon
    from azure_oidc.integrations.falcon_middleware import FalconOIDCAuthMiddleware

    class Echo:
        auth_scopes = "transactions:write"

        def on_post(self, req: falcon.Request, resp: falcon.Response):
            resp.media = req.media

    class EchoNoAuth:
        auth_disable = True

        def on_post(self, req: falcon.Request, resp: falcon.Response):
            resp.media = req.media

    api = falcon.API(middleware=[FalconOIDCAuthMiddleware(config)])
    api.add_route("/echo", Echo())
    api.add_route("/echo-noauth", EchoNoAuth())

    return api


def create_flask_app() -> t.Any:
    from flask import Flask, request
    from azure_oidc.integrations.flask_decorator import FlaskOIDCAuthDecorator, HTTPUnauthorized

    requires_auth = FlaskOIDCAuthDecorator(config)

    api = Flask(__name__)

    @api.route("/echo", methods=["POST"])
    @requires_auth(auth_scopes="transactions:write")
    def echo():
        return request.json

    @api.route("/echo-noauth", methods=["POST"])
    def echo_noauth():
        return request.json

    @api.errorhandler(HTTPUnauthorized)
    def handle_unauthorized(error: HTTPUnauthorized):
        return {"title": "401 Unauthorized", "description": error.description}, 401

    return api


class AppType(Enum):
    FALCON = "falcon"
    FLASK = "flask"


def create_app(app_type: AppType) -> t.Any:
    return {AppType.FALCON: create_falcon_app, AppType.FLASK: create_flask_app}[app_type]()


def serve_app(app):
    from werkzeug.serving import run_simple

    run_simple("0.0.0.0", 6502, app, True, True)


@click.command()
@click.option("--apptype", type=click.Choice([at.value for at in AppType]), default=AppType.FALCON.value)
def serve(apptype: AppType):
    serve_app(create_app(AppType(apptype)))


if __name__ == "__main__":
    serve()
