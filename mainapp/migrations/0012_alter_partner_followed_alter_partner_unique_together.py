# Generated by Django 4.0.3 on 2022-04-20 11:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mainapp', '0011_rename_following_partner_followed'),
    ]

    operations = [
        migrations.AlterField(
            model_name='partner',
            name='followed',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='followed', to='mainapp.profile'),
        ),
        migrations.AlterUniqueTogether(
            name='partner',
            unique_together={('followed', 'follower')},
        ),
    ]
