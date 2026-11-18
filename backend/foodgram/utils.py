"""Вспомогательные функции, общие для сериализаторов."""


def get_file_url(obj, field_name, request):
    """Возвращает абсолютную ссылку на файл или None."""
    file = getattr(obj, field_name, None)
    if not file:
        return None
    try:
        url = file.url
    except ValueError:
        return None
    if request is not None:
        return request.build_absolute_uri(url)
    return url
