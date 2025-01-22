# Generated by Django 5.0.4 on 2024-05-11 09:42

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('eapp', '0011_purchaseorderitem_totalamount_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='cost',
            field=models.DecimalField(decimal_places=2, default=100, max_digits=6),
        ),
        migrations.AddField(
            model_name='product',
            name='sku',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.CreateModel(
            name='AdminMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField()),
                ('confirmed', models.BooleanField(default=False)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='eapp.product')),
                ('purchase_order', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='eapp.purchaseorder')),
            ],
        ),
    ]
