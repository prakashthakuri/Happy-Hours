# Generated by Django 2.2 on 2019-11-28 05:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0022_order_coupon'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='reviews',
            field=models.FloatField(default=1),
            preserve_default=False,
        ),
    ]
