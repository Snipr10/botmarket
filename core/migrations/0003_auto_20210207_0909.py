# Generated by Django 3.1.4 on 2021-02-07 09:09

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_auto_20210207_0840'),
    ]

    operations = [
        migrations.CreateModel(
            name='BotRating',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating', models.IntegerField(validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(5)])),
                ('bot', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.bot')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.usertg')),
            ],
        ),
        migrations.DeleteModel(
            name='BotView',
        ),
    ]
