# Generated by Django 3.2.18 on 2023-07-05 11:39

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('monitor', '0002_auto_20230705_1124'),
    ]

    operations = [
        migrations.RenameField(
            model_name='systemslogs',
            old_name='completed',
            new_name='solved',
        ),
    ]