from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.urls import reverse
from django.utils import timezone

from .validators import validate_age


class Category(models.Model):
    title = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = 'categories'


class Seller(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255, null=True)
    address = models.CharField(max_length=255, null=True)
    website = models.CharField(max_length=255, null=True)

    def __str__(self):
        return f'{self.first_name, self.last_name}'


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    tags = ArrayField(models.CharField(max_length=255))

    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    width = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)
    depth = models.IntegerField(null=True, blank=True)
    weight = models.IntegerField(null=True, blank=True)
    image = models.ImageField(null=True, blank=True)
    date_created = models.DateField(default=timezone.now().date())
    archived = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.title}'

    def get_absolute_url(self) -> str:
        return reverse('product-detail', args=[str(self.id)])

    def get_tags(self) -> set:
        return {tag.tag_name for tag in self.tags.all()}


class ProductInstance(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    seller = models.ForeignKey(Seller, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    amount = models.IntegerField(null=True)

    def __str__(self):
        return f'{self.product.title}'


class Tag(models.Model):
    tag_name = models.CharField(max_length=255)

    def __str__(self):
        return f'{self.tag_name}'


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    birth_date = models.DateField(validators=[validate_age], default=timezone.now().date())
    phone_number = models.CharField(max_length=15, null=True)
    avatar = models.ImageField(null=True, blank=True, upload_to='avatars/')

    def __str__(self):
        return self.user.username


class Subscriber(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username


class SMSLog(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=4, null=True)
    server_response = models.TextField(null=True)

    def __str__(self):
        return self.user.username
