import argparse
import http.server
import multiprocessing
import shutil
import socketserver
import subprocess
import sys
from pathlib import Path

from termcolor import colored


def redisServer():
    subprocess.run(["redis-server"], check=True)


def celeryServer():
    subprocess.run(["./celery.sh"], check=True)


def uvicornServer(ip="127.0.0.1", port=5000, env="prod"):
    # For apiKey initialization
    cur_dir = Path.cwd()
    api_keys_file = cur_dir / "factories" / "apikeys.json"
    api_keys_default = cur_dir / "factories" / "apikeys_default.json"

    if not api_keys_file.is_file():
        shutil.copy(api_keys_default, api_keys_file)

    import uvicorn

    debug = env != "prod"
    uvicorn.run(
        "main:app",
        host=ip,
        port=port,
        reload=debug,
        log_level="info",
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

        print(colored("Uvicorn serving...", "yellow"))
        sys.stdout.flush()
        kwargs_uvicorn = {"ip": ip, "port": 5000}
        uvicorn_proc = multiprocessing.Process(
            name="uvicorn", target=uvicornServer, kwargs=kwargs_uvicorn
        )
        uvicorn_proc.daemon = True

        print(colored("HTTPD serving...", "magenta"))
        sys.stdout.flush()
        httpd_proc = multiprocessing.Process(name="httpd", target=httpServer)
        httpd_proc.daemon = True

        redis_proc.start()
        celery_proc.start()
        uvicorn_proc.start()
        httpd_proc.start()
        redis_proc.join()
        uvicorn_proc.join()
        celery_proc.join()
        httpd_proc.join()
    else:
        uvicornServer(ip, env="desa")
