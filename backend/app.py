# -*- encoding: utf-8 -*-
from factories.application import create_application
import os
import shutil


def run():

    # For apiKey initialization
    cur_dir = os.getcwd()
    api_keys_file = cur_dir + '/factories/apikeys.json'
    api_keys_default = cur_dir + '/factories/apikeys_default.json'

    if (not os.path.exists(api_keys_file) and not
            os.path.isfile(api_keys_file)):
        shutil.copy(api_keys_default, api_keys_file)

    app = create_application()
    # port = int(environ.get("PORT", 5000))
    app.run(host='127.0.0.1', port=5000, debug=True)


if __name__ == '__main__':
    run()
