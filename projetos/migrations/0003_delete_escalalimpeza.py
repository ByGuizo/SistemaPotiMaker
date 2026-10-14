from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('projetos', '0002_initial'),
    ]

    operations = [
        migrations.DeleteModel(
            name='EscalaLimpeza',
        ),
    ]
