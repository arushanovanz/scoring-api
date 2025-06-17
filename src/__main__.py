from http.server import HTTPServer
from src.handlers import MainHTTPHandler
import logging
from argparse import ArgumentParser

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname).1s %(message)s',
    datefmt='%Y.%m.%d %H:%M:%S'
)


def main():
    parser = ArgumentParser(description='Scoring API HTTP Server')
    parser.add_argument('-p', '--port', type=int, default=8080, help='Port to listen on')
    parser.add_argument('-H', '--host', default='0.0.0.0', help='Host to bind to')
    args = parser.parse_args()

    server = HTTPServer((args.host, args.port), MainHTTPHandler)
    logging.info(f'Starting server on {args.host}:{args.port}')

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logging.info('Server stopped')
    finally:
        server.server_close()


if __name__ == '__main__':
    main()