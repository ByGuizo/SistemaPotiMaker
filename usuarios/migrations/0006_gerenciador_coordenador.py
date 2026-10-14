import usuarios.models
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0005_usuario_biografia_usuario_foto_usuario_lattes'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='usuario',
            managers=[
                ('objects', usuarios.models.UsuarioManager()),
            ],
        ),
    ]
