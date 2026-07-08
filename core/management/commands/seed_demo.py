from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from agenda.models import Evento
from inventario.models import Item
from projetos.models import Projeto
from usuarios.models import HorarioEscala, RegistroPresenca

Usuario = get_user_model()


class Command(BaseCommand):
    help = 'Popula o banco com dados de exemplo do PotiMaker.'

    def handle(self, *args, **options):
        hoje = timezone.localdate()

        usuarios_info = [
            ('joao.silva', 'João', 'Silva', Usuario.Tipo.COORDENADOR, '2024001'),
            ('maria.santos', 'Maria', 'Santos', Usuario.Tipo.MEMBRO, '2024002'),
            ('pedro.costa', 'Pedro', 'Costa', Usuario.Tipo.MEMBRO, '2024003'),
            ('ana.lima', 'Ana', 'Lima', Usuario.Tipo.MEMBRO, '2024004'),
            ('carlos.souza', 'Carlos', 'Souza', Usuario.Tipo.MEMBRO, '2024005'),
            ('byguizo', 'ByGuizo', '', Usuario.Tipo.COORDENADOR, '2024006'),
            ('diego', 'Diego', '', Usuario.Tipo.MEMBRO, '2024007'),
            ('fernanda.oliveira', 'Fernanda', 'Oliveira', Usuario.Tipo.MEMBRO, '2024008'),
            ('lucas.pereira', 'Lucas', 'Pereira', Usuario.Tipo.MEMBRO, '2024009'),
            # Equipe Gestora 2026.1 do PotiMaker (cronograma de horários)
            ('luiz.miguel', 'Luiz', 'Miguel', Usuario.Tipo.MEMBRO, '2026001'),
            ('ronald', 'Ronald', '', Usuario.Tipo.MEMBRO, '2026002'),
            ('guyllerme', 'Guyllerme', '', Usuario.Tipo.MEMBRO, '2026003'),
            ('ana.pimentel', 'Ana', 'Pimentel', Usuario.Tipo.MEMBRO, '2026004'),
            ('adi.hillary', 'Adi', 'Hillary', Usuario.Tipo.MEMBRO, '2026005'),
            ('luiz.otavio', 'Luiz', 'Otávio', Usuario.Tipo.MEMBRO, '2026006'),
            ('joao.daniel', 'João', 'Daniel', Usuario.Tipo.MEMBRO, '2026007'),
            ('joadyson', 'Joadyson', '', Usuario.Tipo.MEMBRO, '2026008'),
            ('reinaldo', 'Reinaldo', '', Usuario.Tipo.MEMBRO, '2026009'),
            ('aila', 'Aila', '', Usuario.Tipo.MEMBRO, '2026010'),
            ('josue', 'Josué', '', Usuario.Tipo.MEMBRO, '2026011'),
            ('kaenio', 'Kaênio', '', Usuario.Tipo.MEMBRO, '2026012'),
        ]
        usuarios = {}
        for username, nome, sobrenome, tipo, matricula in usuarios_info:
            usuario, criado = Usuario.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': nome, 'last_name': sobrenome, 'tipo': tipo,
                    'matricula': matricula, 'email': f'{username}@potimaker.ifrn.edu.br',
                }
            )
            if criado:
                usuario.set_password('potimaker123')
                usuario.save()
            usuarios[username] = usuario
        self.stdout.write(self.style.SUCCESS(f'{len(usuarios)} usuários prontos (senha: potimaker123).'))

        itens = [
            ('Arduino Uno R3', Item.Categoria.ELETRONICO, 15, Item.Status.DISPONIVEL),
            ('Arduino', Item.Categoria.ELETRONICO, 1, Item.Status.EM_USO),
            ('Raspberry Pi 4', Item.Categoria.ELETRONICO, 4, Item.Status.DISPONIVEL),
            ('Sensor Ultrassônico HC-SR04', Item.Categoria.ELETRONICO, 20, Item.Status.DISPONIVEL),
            ('Chave de Fenda Phillips', Item.Categoria.FERRAMENTA, 8, Item.Status.DISPONIVEL),
            ('Multímetro Digital', Item.Categoria.FERRAMENTA, 5, Item.Status.EM_USO),
            ('Soldador de Estanho', Item.Categoria.FERRAMENTA, 6, Item.Status.MANUTENCAO),
            ('Filamento PLA 1kg', Item.Categoria.CONSUMIVEL, 12, Item.Status.DISPONIVEL),
            ('Kit Robótica Educacional', Item.Categoria.EQUIPAMENTO, 3, Item.Status.DISPONIVEL),
            ('Scanner 3D', Item.Categoria.EQUIPAMENTO, 1, Item.Status.DISPONIVEL),
            ('Impressora 3D Ender 3', Item.Categoria.EQUIPAMENTO, 2, Item.Status.DISPONIVEL),
        ]
        for nome, categoria, quantidade, status in itens:
            Item.objects.get_or_create(
                nome=nome, defaults={'categoria': categoria, 'quantidade': quantidade, 'status': status}
            )
        self.stdout.write(self.style.SUCCESS(f'{len(itens)} itens de inventário prontos.'))

        projetos = [
            ('Braço Robótico', 'Braço articulado controlado por Arduino', Projeto.Status.A_FAZER,
             Projeto.Prioridade.MEDIA, None, ['joao.silva']),
            ('Sistema de Irrigação IoT', 'Monitoramento automatizado de irrigação', Projeto.Status.A_FAZER,
             Projeto.Prioridade.MEDIA, hoje + timedelta(days=23), ['ana.lima', 'carlos.souza']),
            ('Protese', '', Projeto.Status.FAZENDO, Projeto.Prioridade.MEDIA,
             hoje + timedelta(days=15), []),
            ('Impressão 3D — Peças Reposição', 'Imprimir peças de reposição para equipamentos do lab',
             Projeto.Status.FAZENDO, Projeto.Prioridade.BAIXA, None, ['pedro.costa']),
            ('Robô Seguidor de Linha', 'Construção de robô autônomo para competição', Projeto.Status.FAZENDO,
             Projeto.Prioridade.ALTA, hoje + timedelta(days=7), ['joao.silva', 'pedro.costa']),
            ('Drone de Mapeamento', 'Drone para mapeamento aéreo do campus', Projeto.Status.FAZENDO,
             Projeto.Prioridade.ALTA, hoje - timedelta(days=1), ['maria.santos', 'lucas.pereira']),
            ('Estação Meteorológica', 'Estação com sensores conectados', Projeto.Status.CONCLUIDO,
             Projeto.Prioridade.BAIXA, None, ['fernanda.oliveira']),
        ]
        for nome, descricao, status, prioridade, prazo, membros_usernames in projetos:
            projeto, _ = Projeto.objects.get_or_create(
                nome=nome,
                defaults={'descricao': descricao, 'status': status, 'prioridade': prioridade, 'prazo': prazo},
            )
            if membros_usernames:
                projeto.membros.set([usuarios[u] for u in membros_usernames])
        self.stdout.write(self.style.SUCCESS(f'{len(projetos)} projetos prontos.'))

        eventos = [
            ('Oficina de Solda', hoje + timedelta(days=2), 'Laboratório PotiMaker'),
            ('Reunião de Coordenação', hoje + timedelta(days=5), 'Sala de Reuniões'),
            ('Feira de Robótica IFRN', hoje + timedelta(days=20), 'Auditório Central'),
        ]
        for titulo, data, local in eventos:
            Evento.objects.get_or_create(
                titulo=titulo, data=data, defaults={'local': local, 'criado_por': usuarios['joao.silva']}
            )
        self.stdout.write(self.style.SUCCESS(f'{len(eventos)} eventos prontos.'))

        for username in ['byguizo', 'diego']:
            if not RegistroPresenca.objects.filter(usuario=usuarios[username]).exists():
                RegistroPresenca.objects.create(usuario=usuarios[username])
        self.stdout.write(self.style.SUCCESS('Registros de presença de exemplo prontos.'))

        # Escala de horários — Equipe Gestora PotiMaker 2026.1 (cronograma do laboratório)
        SEG, TER, QUA, QUI, SEX = (
            HorarioEscala.DiaSemana.SEGUNDA, HorarioEscala.DiaSemana.TERCA,
            HorarioEscala.DiaSemana.QUARTA, HorarioEscala.DiaSemana.QUINTA, HorarioEscala.DiaSemana.SEXTA,
        )
        M1, M2, M3 = HorarioEscala.Slot.M1, HorarioEscala.Slot.M2, HorarioEscala.Slot.M3
        T1, T2, T3 = HorarioEscala.Slot.T1, HorarioEscala.Slot.T2, HorarioEscala.Slot.T3

        escala_info = [
            (SEG, M1, ['luiz.miguel']),
            (TER, M1, ['ana.pimentel', 'guyllerme']),
            (QUA, M1, ['luiz.otavio', 'adi.hillary']),
            (QUI, M1, ['ana.pimentel', 'guyllerme']),
            (SEX, M1, ['luiz.miguel']),

            (SEG, M2, ['luiz.miguel']),
            (TER, M2, ['ana.pimentel', 'guyllerme']),
            (QUA, M2, ['luiz.otavio', 'adi.hillary']),
            (QUI, M2, ['ana.pimentel', 'guyllerme']),
            (SEX, M2, ['luiz.miguel', 'ana.pimentel']),

            (SEG, M3, ['luiz.miguel', 'ronald']),
            (TER, M3, ['guyllerme']),
            (QUA, M3, ['luiz.otavio', 'adi.hillary']),
            (QUI, M3, ['ana.pimentel', 'guyllerme']),
            (SEX, M3, ['luiz.miguel', 'ronald']),

            (SEG, T1, ['joao.daniel', 'aila']),
            (TER, T1, ['joadyson', 'reinaldo']),
            (QUA, T1, ['byguizo', 'diego']),
            (QUI, T1, ['aila', 'diego']),
            (SEX, T1, ['reinaldo', 'aila']),

            (SEG, T2, ['joao.daniel', 'reinaldo']),
            (TER, T2, ['joadyson', 'reinaldo']),
            (QUA, T2, ['byguizo', 'diego']),
            (QUI, T2, ['diego', 'byguizo']),
            (SEX, T2, ['reinaldo', 'aila']),

            (SEG, T3, ['reinaldo']),
            (TER, T3, ['joadyson', 'joao.daniel']),
            (QUA, T3, ['byguizo', 'diego']),
            (QUI, T3, ['josue', 'diego']),
            (SEX, T3, ['josue', 'kaenio']),
        ]
        for dia, slot, membros_usernames in escala_info:
            horario, _criado = HorarioEscala.objects.get_or_create(dia_semana=dia, slot=slot)
            horario.membros.set([usuarios[u] for u in membros_usernames])
        self.stdout.write(self.style.SUCCESS(f'{len(escala_info)} horários da escala prontos.'))

        self.stdout.write(self.style.SUCCESS('Seed concluído com sucesso.'))
