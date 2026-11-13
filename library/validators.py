"""Small reusable model/serializer field validators."""
import re

from django.core.exceptions import ValidationError


def validate_isbn13(value):
    """Accept exactly 13 digits with a valid ISBN-13 check digit."""
    value = str(value)
    if len(value) != 13 or not value.isascii() or not value.isdigit():
        raise ValidationError('ISBN must contain exactly 13 digits.')
    weighted_sum = sum(
        int(digit) * (1 if index % 2 == 0 else 3)
        for index, digit in enumerate(value[:12])
    )
    check_digit = (10 - weighted_sum % 10) % 10
    if int(value[-1]) != check_digit:
        raise ValidationError('Invalid ISBN-13 check digit.')


def validate_membership_id(value):
    if not re.fullmatch(r'LIB-\d{4}', value):
        raise ValidationError('Membership ID must look like LIB-0001.')
