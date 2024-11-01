# Generated by Django 5.0.6 on 2024-10-27 23:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_wallet', '0017_remove_transaction_user_operation_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='operation',
            name='balance_after',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=15),
        ),
        migrations.AlterField(
            model_name='operation',
            name='balance_before',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=15),
        ),
    ]