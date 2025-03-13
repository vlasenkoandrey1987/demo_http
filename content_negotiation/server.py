import enum
import gzip
import http.server
import io
import os
from http import HTTPStatus

DEFAULT_LANGUAGE = 'en'


class Compression(enum.Enum):
    gzip = 'gz'


class Content:

    def __init__(self, file_path, compression):
        self.file = None
        self._length = None
        self.last_modified = None

        try:
            file = open(file_path, 'rb')
        except OSError:
            pass
        else:
            stat = os.fstat(file.fileno())
            self.last_modified = stat.st_mtime

            if not compression:
                self.file = file
                self._length = stat[6]
            else:
                if compression is Compression.gzip:
                    content = gzip.compress(file.read())
                    self.file = io.BytesIO(content)
                    self._length = len(content)

                file.close()

    def __bool__(self):
        return self.file is not None

    def __len__(self):
        return self._length


class HTTPRequestHandler(http.server.SimpleHTTPRequestHandler):

    def do_GET(self):
        path = self._get_path()

        language = self._get_language()
        if not language:
            self.send_error(
                HTTPStatus.NOT_ACCEPTABLE,
                f'Languages [{self.headers.get("Accept-Language", "")}] '
                f'not supported',
            )

        compression = self._get_compression()

        path = self._specify_path_with_language(path, language)

        content = Content(path, compression)
        if not content:
            self.send_error(HTTPStatus.NOT_FOUND, 'File not found')

        self.send_response(HTTPStatus.OK)
        self.send_header(
            'Content-Type', f'{self.guess_type(path)};charset=utf-8'
        )
        self.send_header('Content-Language', language)
        if compression:
            self.send_header('Content-Encoding', compression.name)
        self.send_header('Content-Length', str(len(content)))
        self.send_header('Content-Location', path)
        self.send_header(
            'Last-Modified', self.date_time_string(content.last_modified)
        )
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()

        try:
            self.copyfile(content.file, self.wfile)
        finally:
            content.file.close()

    def _get_path(self):
        path = self.translate_path(self.path)

        if os.path.isdir(path):
            path = os.path.join(path, 'index.html')

        if path.endswith('/'):
            self.send_error(HTTPStatus.NOT_FOUND, 'File not found')
            return None

        return path

    def _get_language(self):
        """Просматривает заголовок Accept-Language (если он передан) слева
        направо, первый язык, для которого найдена директория, будет возвращен.
        """
        if 'Accept-Language' not in self.headers:
            return DEFAULT_LANGUAGE

        language = None
        for lang in self.headers.get('Accept-Language', '').split(','):
            if '-' in lang:
                continue

            if ';' in lang:
                lang = lang.split(';')[0]

            path = os.path.join(os.getcwd(), lang.strip())
            if os.path.exists(path):
                language = lang
                break

        return language

    @staticmethod
    def _specify_path_with_language(path, language):
        path = os.path.split(path)
        return os.path.join(path[0], language, path[1])

    def _get_compression(self):
        compression = None
        for comp in self.headers.get('Accept-Encoding', '').split(','):
            if comp.strip() in Compression.__members__:
                compression = getattr(Compression, comp, None)
                if compression:
                    break

        return compression


def run_server(port):
    Handler = HTTPRequestHandler

    with http.server.HTTPServer(('', port), Handler) as httpd:
        print('serving at port', port)
        httpd.serve_forever()


if __name__ == '__main__':
    run_server(80)
