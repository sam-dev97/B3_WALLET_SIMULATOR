# Generated by Django 5.0.6 on 2024-06-30 17:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_wallet', '0009_alter_stockdata_unique_together_transaction'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='quantity',
            field=models.IntegerField(default=0),
        ),
    ]
