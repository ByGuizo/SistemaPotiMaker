import sqlite3
from contextlib import closing
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.utils import timezone

PREFIXO = 'db_'
EXTENSAO = '.sqlite3'


class Command(BaseCommand):
    help = (
        'Copia o banco SQLite para backups/ com data e hora no nome, usando a API de '
        'backup do SQLite (seguro com o sistema rodando), e apaga as cópias mais antigas.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--manter', type=int, default=30, metavar='N',
            help='Quantas cópias manter na pasta de backups, contando a nova (padrão: 30).',
        )

    def handle(self, *args, **options):
        manter = options['manter']
        if manter < 1:
            raise CommandError('--manter precisa ser pelo menos 1. Nada foi feito.')
        if connection.vendor != 'sqlite':
            raise CommandError('Este comando só funciona com SQLite. Nada foi feito.')

        pasta = Path(settings.BACKUP_DIR)
        pasta.mkdir(parents=True, exist_ok=True)

        carimbo = timezone.localtime().strftime('%Y-%m-%d_%H-%M-%S')
        destino = pasta / f'{PREFIXO}{carimbo}{EXTENSAO}'
        if destino.exists():
            raise CommandError(f'{destino.name} já existe (dois backups no mesmo segundo). Nada foi feito.')
        temporario = destino.with_name(destino.name + '.parcial')

        connection.ensure_connection()
        try:
            with closing(sqlite3.connect(temporario)) as copia:
                connection.connection.backup(copia)
                resultado = copia.execute('PRAGMA integrity_check').fetchone()[0]
            if resultado != 'ok':
                raise CommandError(f'A cópia não passou na verificação de integridade: {resultado}')
            temporario.replace(destino)
        finally:
            temporario.unlink(missing_ok=True)

        tamanho_kb = destino.stat().st_size / 1024
        self.stdout.write(self.style.SUCCESS(f'Backup criado: {destino} ({tamanho_kb:.0f} KB)'))

        backups = sorted(pasta.glob(f'{PREFIXO}*{EXTENSAO}'))
        antigos = backups[:-manter]
        for arquivo in antigos:
            arquivo.unlink()
        if antigos:
            self.stdout.write(f'Removidos {len(antigos)} backup(s) antigo(s); mantidos {manter}.')
