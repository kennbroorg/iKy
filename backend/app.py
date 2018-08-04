# -*- encoding: utf-8 -*-
from factories.application import create_application
import os
import shutil
import argparse


def run(ip='127.0.0.1'):

    # For apiKey initialization
    cur_dir = os.getcwd()
    api_keys_file = cur_dir + '/factories/apikeys.json'
    api_keys_default = cur_dir + '/factories/apikeys_default.json'

    if (not os.path.exists(api_keys_file) and not
            os.path.isfile(api_keys_file)):
        shutil.copy(api_keys_default, api_keys_file)

    app = create_application()
    # port = int(environ.get("PORT", 5000))
    app.run(host=ip, port=5000, debug=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--ip', action='store', default='127.0.0.1',
                        help='IP address, just for vagrant')

    args = parser.parse_args()
    ip = str(args.ip)
    run(ip)
