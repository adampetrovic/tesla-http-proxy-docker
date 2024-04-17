import os
import sys
import uuid
import logging
import argparse
import requests
from flask import Flask, request, render_template, cli, redirect, send_from_directory
from werkzeug.exceptions import HTTPException

logging.basicConfig(
    format="[%(asctime)s] %(name)s:%(levelname)s: %(message)s",
    level=logging.INFO,
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("main")

app = Flask(__name__)

SCOPES = "openid offline_access vehicle_device_data vehicle_cmds vehicle_charging_cmds"
AUDIENCES = {
    "North America, Asia-Pacific": "https://fleet-api.prd.na.vn.cloud.tesla.com",
    "Europe, Middle East, Africa": "https://fleet-api.prd.eu.vn.cloud.tesla.com",
    "China": "https://fleet-api.prd.cn.vn.cloud.tesla.cn",
}

parser = argparse.ArgumentParser()

parser.add_argument(
    "--client-id",
    help="Client ID. Required if not provided in environment variable CLIENT_ID",
    default=os.environ.get("CLIENT_ID"),
)
parser.add_argument(
    "--client-secret",
    help="Client secret. Required if not provided in environment variable CLIENT_SECRET",
    default=os.environ.get("CLIENT_SECRET"),
)
parser.add_argument(
    "--domain",
    help="Domain. Required if not provided in environment variable DOMAIN",
    default=os.environ.get("DOMAIN"),
)
parser.add_argument(
    "--region",
    choices=AUDIENCES.keys(),
    help="Region. Required if not provided in environment variable REGION",
    default=os.environ.get("REGION"),
)
parser.add_argument(
    "--config-base",
    help="Config base path. Required if not provided in environment variable CONFIG_BASE",
    default=os.environ.get("CONFIG_BASE"),
)

args = parser.parse_args()

if (
    not args.client_id
    or not args.client_secret
    or not args.domain
    or not args.region
    or not args.config_base
):
    parser.print_help()
    sys.exit(1)


@app.errorhandler(Exception)
def handle_exception(e):
    """Exception handler for HTTP requests"""
    logger.error(e)
    # pass through HTTP errors
    if isinstance(e, HTTPException):
        return e

    # now you're handling non-HTTP exceptions only
    return "Unknown Error", 500


@app.route("/")
def index():
    """Web UI"""
    return render_template(
        "index.html",
        domain=args.domain,
        client_id=args.client_id,
        scopes=SCOPES,
        randomstate=uuid.uuid4().hex,
        randomnonce=uuid.uuid4().hex,
    )


@app.route("/callback")
def callback():
    """Handle POST callback from Tesla server to complete OAuth"""
    logger.info("callback args: %s", request.args)
    # sometimes I don't get a valid code, not sure why
    try:
        code = request.args["code"]
    except KeyError:
        logger.error("args: %s", request.args)
        return "Invalid code!", 400

    # Exchange code for refresh_token
    req = requests.post(
        "https://auth.tesla.com/oauth2/v3/token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "authorization_code",
            "client_id": args.client_id,
            "client_secret": args.client_secret,
            "code": code,
            "audience": AUDIENCES[args.region],
            "redirect_uri": f"https://{args.domain}/callback",
        },
        timeout=30,
    )

    output = (
        "Info to enter into Tesla Custom component:\n"
        f"Refresh token  : {req.json()['refresh_token']}\n"
        f"Proxy URL      : https://{args.domain}\n"
        f"SSL certificate: {args.config_base}/tesla-proxy/cert.pem\n"
        f"Client ID      : {args.client_id}\n"
    )

    logger.info(output)

    req.raise_for_status()
    return render_template("callback.html")


@app.route("/register-partner-account")
def register_partner_account():
    """Register the partner account with Tesla API to enable API access"""

    logger.info("*** Generating Partner Authentication Token ***")

    req = requests.post(
        "https://auth.tesla.com/oauth2/v3/token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "client_credentials",
            "client_id": args.client_id,
            "client_secret": args.client_secret,
            "scope": SCOPES,
            "audience": AUDIENCES[args.region],
        },
        timeout=30,
    )
    if req.status_code >= 400:
        logger.error("HTTP %s: %s", req.status_code, req.reason)
        return redirect(f"/?error={req.status_code}", code=302)

    logger.info(req.text)
    tesla_api_token = req.json()["access_token"]

    # register Tesla account to enable API access
    logger.info("*** Registering Tesla account ***")
    req = requests.post(
        f"{AUDIENCES[args.region]}/api/1/partner_accounts",
        headers={
            "Authorization": "Bearer " + tesla_api_token,
            "Content-Type": "application/json",
        },
        data='{"domain": "%s"}' % args.domain,
        timeout=30,
    )
    if req.status_code >= 400:
        logger.error("Error %s: %s", req.status_code, req.reason)
        return redirect(f"/?error={req.status_code}", code=302)
    logger.info(req.text)

    return redirect("/?success=1", code=302)


if __name__ == "__main__":
    logger.info("*** Starting Flask setup server... ***")
    cli.show_server_banner = lambda *_: None
    app.run(port=8099, debug=False, host="0.0.0.0")
