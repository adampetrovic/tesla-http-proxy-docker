import os
import sys
import argparse
import logging
from flask import Flask, cli, send_from_directory


logging.basicConfig(
    format="[%(asctime)s] %(name)s:%(levelname)s: %(message)s",
    level=logging.INFO,
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("main")

app = Flask(__name__)
parser = argparse.ArgumentParser()


parser.add_argument(
    "--config-base",
    help="Config base path. Required if not provided in environment variable CONFIG_BASE",
    default=os.environ.get("CONFIG_BASE"),
)

args = parser.parse_args()

if not args.config_base:
    parser.print_help()
    sys.exit(1)


@app.route("/.well-known/appspecific/com.tesla.3p.public-key.pem")
def public_key():
    return send_from_directory(f"{args.config_base}/tesla", "com.tesla.3p.public-key.pem")


if __name__ == "__main__":
    logger.info("*** Starting Flask keyserver... ***")
    cli.show_server_banner = lambda *_: None
    app.run(port=8098, debug=False, host="0.0.0.0")
