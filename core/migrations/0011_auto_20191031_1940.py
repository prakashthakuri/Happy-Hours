# Generated by Django 2.2 on 2019-10-31 23:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_merge_20191030_1225'),
    ]

    operations = [
        migrations.AlterField(
            model_name='item',
            name='category',
            field=models.CharField(choices=[('B', 'Beer'), ('W', 'Wine'), ('L', 'Liquor'), ('W', 'Whiskey')], max_length=2),
        ),
    ]
