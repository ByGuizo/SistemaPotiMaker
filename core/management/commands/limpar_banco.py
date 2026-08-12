from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from agenda.models import Evento
from inventario.models import Item
from projetos.models import Atividade, Projeto
from usuarios.models import HorarioEscala, RegistroPresenca

Usuario = get_user_model()

# Contas preservadas por padrão. Todo o resto é apagado.
USUARIOS_PADRAO = ['admin', 'byguizo']


class Command(BaseCommand):
    help = (
        'Esvazia o banco (inventário, projetos, atividades, eventos, escala, presenças) '
        'e remove todos os usuários, exceto os preservados. Ação destrutiva e irreversível.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--sim', action='store_true',
            help='Confirma a exclusão. Sem esta flag o comando apenas mostra o que seria apagado.',
        )
        parser.add_argument(
            '--manter', nargs='*', metavar='USERNAME', default=None,
            help=f'Usernames a preservar (padrão: {" ".join(USUARIOS_PADRAO)}).',
        )

    def handle(self, *args, **options):
        manter = options['manter'] if options['manter'] is not None else USUARIOS_PADRAO
        preservados = Usuario.objects.filter(username__in=manter)
        a_remover = Usuario.objects.exclude(username__in=manter)

        faltando = set(manter) - set(preservados.values_list('username', flat=True))
        if faltando:
            raise CommandError(
                f'Usuário(s) a preservar não existem: {", ".join(sorted(faltando))}. '
                'Nada foi apagado.'
            )

        contagens = {
            'Itens de inventário': Item.objects.count(),
            'Atividades': Atividade.objects.count(),
            'Projetos': Projeto.objects.count(),
            'Eventos': Evento.objects.count(),
            'Registros de presença': RegistroPresenca.objects.count(),
            'Células da escala': HorarioEscala.objects.count(),
            'Usuários': a_remover.count(),
        }

        self.stdout.write(self.style.WARNING('Será apagado:'))
        for rotulo, qtd in contagens.items():
            self.stdout.write(f'  {rotulo}: {qtd}')
        self.stdout.write(
            'Preservados: ' + ', '.join(sorted(preservados.values_list('username', flat=True)))
        )

        if not options['sim']:
            self.stdout.write(self.style.NOTICE(
                '\nNada foi apagado (simulação). Rode com --sim para confirmar.'
            ))
            return

        with transaction.atomic():
            # Atividade antes de Projeto: a FK é CASCADE, mas explicitar deixa a
            # ordem clara e não depende do comportamento do banco.
            Item.objects.all().delete()
            Atividade.objects.all().delete()
            Projeto.objects.all().delete()
            Evento.objects.all().delete()
            RegistroPresenca.objects.all().delete()
            HorarioEscala.objects.all().delete()
            a_remover.delete()

        self.stdout.write(self.style.SUCCESS('\nBanco limpo.'))
        self.stdout.write(
            f'Usuários restantes: {", ".join(Usuario.objects.values_list("username", flat=True))}'
        )
