from django.conf import settings
from django.db import models
from django.shortcuts import reverse
from django_countries.fields import CountryField

CATEGORY_CHOICES = (
    ('B', 'Beer'),
    ('W', 'Wine'),
    ('L', 'Liquor'),
    ('W', 'Whiskey')

)

LABEL_CHOICES = (
    ('P', 'primary'),
    ('S', 'secondary'),
    ('D', 'danger')
)
CATEGORY_TYPES = (
    ('N', 'New'),
    ('B', 'Best Seller'),
    ('NY', 'NY Local'),
    ('S', 'Staff Pick'),
    ('P', 'Most Popular'),
    ('H', 'Holiday Pick'),
    ('BL', '')
)
# ------------------------------------ For R2
CATEGORY_SIZES = (
    ('S', '750ml'),
    ('M', '1L'),
    ('L', '1.75L'),
    ('XL', '375ml')
)

CATEGORY_REGION = (
    ('A', 'Asia'),
    ('E', 'England'),
    ('M', 'Mexico'),
    ('I', 'Italy'),
    ('A', 'France'),
    ('S', 'South Asia'),
    ('U', 'United States'),
    ('S', 'Spain'),
    ('R', 'Russia')
)

CATEGORY_ABV = (
    ('5', '5%'),
    ('12', '12%'),
    ('40', '40%'),
    ('8', '8%')
)


class Item(models.Model):
    title = models.CharField(max_length=100)
    price = models.FloatField()
    discount_price = models.FloatField(blank=True, null=True)
    category = models.CharField(choices=CATEGORY_CHOICES, max_length=2)
    label = models.CharField(choices=LABEL_CHOICES, max_length=1)
    types = models.CharField(choices=CATEGORY_TYPES, max_length=2, null=True)

    # Note (Prakash): These features are added for R2
    sizes = models.CharField(choices=CATEGORY_SIZES, max_length=2, null=True)
    region = models.CharField(choices=CATEGORY_REGION, max_length=2, null=True)
    abv = models.CharField(choices=CATEGORY_ABV, max_length=2, null=True)
    features = models.CharField(max_length=1000)
    tasting = models.CharField(max_length=1000)

    # ----------------------------------------------------
    slug = models.SlugField()
    description = models.TextField()
    image = models.ImageField()

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("core:product", kwargs={
            'slug': self.slug
        })

    def get_add_to_cart_url(self):
        return reverse("core:add-to-cart", kwargs={
            'slug': self.slug
        })

    def get_remove_from_cart_url(self):
        return reverse("core:remove-from-cart", kwargs={
            'slug': self.slug
        })


class OrderItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)

    ordered = models.BooleanField(default=False)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} of {self.item.title}"

    def get_total_item_price(self):
        return self.quantity * self.item.price

    def get_total_discount_item_price(self):
        return self.quantity * self.item.discount_price

    def get_amount_saved(self):
        return self.get_total_item_price() - self.get_total_discount_item_price()

    def get_final_price(self):
        if self.item.discount_price:
            return self.get_total_discount_item_price()
        return self.get_total_item_price()


class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    items = models.ManyToManyField(OrderItem)
    start_date = models.DateTimeField(auto_now_add=True)
    ordered_date = models.DateTimeField()
    ordered = models.BooleanField(default=False)
    billing_address = models.ForeignKey('BillingAddress', on_delete=models.SET_NULL, blank=True, null=True)
    payment = models.ForeignKey('Payment', on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return self.user.username

    def get_total(self):
        total = 0
        for order_item in self.items.all():
            total += order_item.get_final_price()
        return total


class BillingAddress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    street_address = models.CharField(max_length=100)
    apartment_address = models.CharField(max_length=100)
    country = CountryField(multiple=False)
    city = models.CharField(max_length=100)
    zip = models.CharField(max_length=100)

    def __str__(self):
        return self.user.username


class Payment(models.Model):
    stripe_charge_id = models.CharField(max_length=50)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True)
    amount = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    @property
    def __str__(self):
        return self.user.username
