import os
from django.core.exceptions import ValidationError


def validate_file_extension(value):
    ext = os.path.splitext(value.name)[1]
    valid_extension = ['.pdf', '.jpg']
    if not ext.lower() in valid_extension:
        raise ValidationError(u'Unsupported extension')