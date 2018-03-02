# -*- encoding: utf-8 -*-
from factories.application import create_application


def run():
    app = create_application()
    #port = int(environ.get("PORT", 5000))
    app.run(host='127.0.0.1', port=5000, debug=True)

if __name__ == '__main__':
    run()
