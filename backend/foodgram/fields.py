import base64
import uuid
from io import BytesIO

from django.core.files.base import ContentFile
from PIL import Image, UnidentifiedImageError
from rest_framework import serializers


class Base64ImageField(serializers.ImageField):
    """Поле картинки, принимающее base64 (в том числе data URL)."""

    def to_internal_value(self, data):
        if not isinstance(data, str):
            return super().to_internal_value(data)

        if data.startswith('data:image'):
            header, _, data = data.partition(';base64,')
            if not data:
                raise serializers.ValidationError(
                    'Некорректный формат изображения.'
                )
            extension = header.split('/')[-1].split(';')[0]
        else:
            extension = ''

        try:
            decoded = base64.b64decode(data, validate=True)
        except (ValueError, TypeError):
            raise serializers.ValidationError(
                'Некорректный формат изображения.'
            )

        try:
            with Image.open(BytesIO(decoded)) as image:
                image_format = (image.format or 'png').lower()
                image.verify()
        except (
            UnidentifiedImageError,
            OSError,
            ValueError,
            SyntaxError,
            Image.DecompressionBombError,
        ):
            raise serializers.ValidationError(
                'Файл не является изображением.'
            )

        return super().to_internal_value(
            ContentFile(
                decoded,
                name=f'{uuid.uuid4()}.{extension or image_format}',
            )
        )
