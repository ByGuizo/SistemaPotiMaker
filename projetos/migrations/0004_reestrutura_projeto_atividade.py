import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def migrar_projetos_para_atividades(apps, schema_editor):
    Projeto = apps.get_model('projetos', 'Projeto')
    Atividade = apps.get_model('projetos', 'Atividade')

    for projeto_antigo in Projeto.objects.all():
        atividade = Atividade.objects.create(
            projeto_id=projeto_antigo.pk,
            nome=projeto_antigo.nome,
            descricao=projeto_antigo.descricao,
            documento_tecnico=projeto_antigo.documento_tecnico,
            status=projeto_antigo.status,
            prioridade=projeto_antigo.prioridade,
            prazo=projeto_antigo.prazo,
        )
        atividade.membros.set(projeto_antigo.membros.all())


def reverter_migracao(apps, schema_editor):
    Atividade = apps.get_model('projetos', 'Atividade')
    Atividade.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('projetos', '0003_delete_escalalimpeza'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Atividade',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=150)),
                ('descricao', models.TextField(blank=True)),
                ('documento_tecnico', models.FileField(blank=True, null=True, upload_to='projetos/docs/')),
                ('status', models.CharField(choices=[('A_FAZER', 'A Fazer'), ('FAZENDO', 'Fazendo'), ('CONCLUIDO', 'Concluído')], default='A_FAZER', max_length=10)),
                ('prioridade', models.CharField(choices=[('BAIXA', 'Baixa'), ('MEDIA', 'Média'), ('ALTA', 'Alta')], default='MEDIA', max_length=6)),
                ('prazo', models.DateField(blank=True, null=True)),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('membros', models.ManyToManyField(blank=True, related_name='atividades', to=settings.AUTH_USER_MODEL)),
                ('projeto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='atividades_temp', to='projetos.projeto')),
            ],
            options={
                'ordering': ['-prioridade', 'prazo'],
            },
        ),
        migrations.RunPython(migrar_projetos_para_atividades, reverter_migracao),
        migrations.RemoveField(model_name='projeto', name='documento_tecnico'),
        migrations.RemoveField(model_name='projeto', name='membros'),
        migrations.RemoveField(model_name='projeto', name='prazo'),
        migrations.RemoveField(model_name='projeto', name='prioridade'),
        migrations.RemoveField(model_name='projeto', name='status'),
        migrations.AlterModelOptions(
            name='projeto',
            options={'ordering': ['nome']},
        ),
        migrations.AlterField(
            model_name='atividade',
            name='projeto',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='atividades', to='projetos.projeto'),
        ),
    ]
