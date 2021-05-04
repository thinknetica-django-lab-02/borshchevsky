from random import randint

import vonage
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank

from main.models import Product
from market.settings import VONAGE_API_KEY, VONAGE_SECRET


def send_sms(phone_number):
    """Sends SMS via Vonage sms-service.
    """
    client = vonage.Client(key=VONAGE_API_KEY, secret=VONAGE_SECRET)
    sms = vonage.Sms(client)
    code = generate_code()
    message = f'Your verification code: {code}'
    response_data = sms.send_message({
        'from': 'Django market',
        'to': phone_number,
        'text': message
    })
    return code, response_data


def generate_code():
    """Returns random 4-digit code.
    """

    return str(randint(1000, 9999)).zfill(4)


def archive(modeladmin, request, queryset):
    """
    function for Product ModelAdmin - archives selected queries
    """
    queryset.update(archived=True)


def publish(modeladmin, request, queryset):
    """
    function for Product ModelAdmin - publishes selected queries
    """
    queryset.update(archived=False)


def search_product(search_text):
    vector = SearchVector('title', weight='A') + SearchVector('description', weight='B')
    query = SearchQuery(search_text)

    # Не нашел как сделать фильтр по вхождению строки
    return Product.objects.annotate(rank=SearchRank(vector, query)).order_by('-rank')


def is_mobile(user_agent):
    """
    detects if particular user_agent is a mobile or not
    """
    words = ['iphone', 'android', 'opera mini']
    return any(word in user_agent for word in words)
