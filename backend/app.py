import argparse
import http.server
import multiprocessing
import shutil
import socketserver
import subprocess
import sys
from pathlib import Path

from factories.application import create_application
from factories.extensions import socketio
from termcolor import colored


def redisServer():
    subprocess.run(["redis-server"], check=True)


def celeryServer():
    subprocess.run(["./celery.sh"], check=True)


def flaskServer(ip="127.0.0.1", port=5000, env="prod"):
    # For apiKey initialization
    cur_dir = Path.cwd()
    api_keys_file = cur_dir / "factories" / "apikeys.json"
    api_keys_default = cur_dir / "factories" / "apikeys_default.json"

    if not api_keys_file.is_file():
        shutil.copy(api_keys_default, api_keys_file)

    app, _sio = create_application()

    debug = env != "prod"
    if env == "prod":
        socketio.run(app, port=port, debug=False, host=ip, use_reloader=False)
    else:
        socketio.run(
            app, host=ip, port=port, debug=debug, allow_unsafe_werkzeug=True
        )


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="../frontend/dist/", **kwargs)


def httpServer():
    PORT = 4200
    # TODO : Add directory validation
    with socketserver.TCPServer(("", PORT), Handler) as httpd_server:
        print(colored("HTTPD serving...INSIDE", "white"))
        httpd_server.serve_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i",
        "--ip",
        action="store",
        default="127.0.0.1",
        help="IP address, just for vagrant",
    )
    parser.add_argument(
        "-e", "--env", action="store", default="dev", help="Environment [dev, prod]"
    )

    args = parser.parse_args()
    ip = str(args.ip)
    env = str(args.env)

    if env == "prod":
        print(colored("Starting PROD servers", "red"))
        sys.stdout.flush()

        print(colored("REDIS serving...", "cyan"))
        sys.stdout.flush()
        redis_proc = multiprocessing.Process(name="redis", target=redisServer)
        redis_proc.daemon = True

        print(colored("CELERY serving...", "blue"))
        sys.stdout.flush()
        celery_proc = multiprocessing.Process(name="celery", target=celeryServer)
        celery_proc.daemon = True

        print(colored("Flask serving...", "yellow"))
        sys.stdout.flush()
        kwargs_flask = {"ip": ip, "port": 5000}
        flask_proc = multiprocessing.Process(
            name="flask", target=flaskServer, kwargs=kwargs_flask
        )
        flask_proc.daemon = True

        print(colored("HTTPD serving...", "magenta"))
        sys.stdout.flush()
        httpd_proc = multiprocessing.Process(name="httpd", target=httpServer)
        httpd_proc.daemon = True

        redis_proc.start()
        celery_proc.start()
        flask_proc.start()
        httpd_proc.start()
        redis_proc.join()
        flask_proc.join()
        celery_proc.join()
        httpd_proc.join()
    else:
        flaskServer(ip, env="desa")
