import requests


def get(port, resource, language, encoding):
    result = requests.get(
        f'http://localhost:{port}/{resource}',
        headers={
            **({'Accept-Language': language} if language is not None else {}),
            **({'Accept-Encoding': encoding} if encoding is not None else {}),
        },
    )
    return result


if __name__ == '__main__':
    """Сценарии для Accept-Language:
    None
    ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7
    ru;q=0.9,en-US;q=0.8,en;q=0.7
    ru,en-US;q=0.9,en;q=0.8
    ru,en
    en
    de
    
    Сценарии для Accept-Encoding:
    None - requests добавит заголовок со значением gzip
    <Пусто>
    gzip
    deflate
    """
    port = 8080
    resource = 'doc.html'
    language = None
    encoding = ''

    result = get(port, resource, language, encoding)

    print('status_code:', result.status_code)
    print('headers:', result.headers)
    print('content:', result.content)
    print('text:', result.text)
