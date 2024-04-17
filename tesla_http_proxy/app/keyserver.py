import os
import sys
import argparse
from flask import Flask, send_from_directory

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
