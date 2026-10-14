from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projetos', '0004_reestrutura_projeto_atividade'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='atividade',
            options={'ordering': [models.OrderBy(models.Case(models.When(prioridade='ALTA', then=models.Value(0)), models.When(prioridade='MEDIA', then=models.Value(1)), models.When(prioridade='BAIXA', then=models.Value(2)), default=models.Value(3), output_field=models.IntegerField())), 'prazo']},
        ),
    ]
