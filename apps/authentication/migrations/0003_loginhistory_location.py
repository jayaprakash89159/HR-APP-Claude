from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0002_alter_loginhistory_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='loginhistory',
            name='location',
            field=models.CharField(blank=True, max_length=200),
        ),
    ]