# Guia de implantação — PotiMaker

Sistema de gestão do FabLab do IFRN Campus Canguaretama. Aplicação Django com
banco SQLite, servida por **gunicorn** atrás do **nginx** com HTTPS.

```
navegador ──HTTPS──> nginx (443) ──HTTP──> gunicorn (127.0.0.1:8000) ──> Django
                       │                                                  │
                  certificado TLS                           db.sqlite3, media/, cache/
```

- O **nginx** termina o HTTPS e repassa tudo para o gunicorn. Ele **não** serve
  nenhuma pasta do projeto diretamente (veja o aviso sobre `media/` na seção 6).
- Os arquivos estáticos (CSS/JS) são servidos pelo próprio Django (WhiteNoise).
- Os arquivos enviados pelos usuários (fotos e documentos em `media/`) passam
  pelo Django, que exige login.

Os comandos abaixo supõem Debian/Ubuntu, o sistema em `/srv/potimaker/app` e um
usuário de sistema `potimaker`. Ajuste caminhos e domínio conforme o ambiente.
O domínio de exemplo é `potimaker.exemplo.ifrn.edu.br`.

---

## 1. Requisitos

| Item | Versão / observação |
|---|---|
| Sistema operacional | Linux (o gunicorn não roda em Windows) |
| Python | 3.12 ou mais recente (exigência do Django 6.0) |
| nginx | qualquer versão atual |
| Certificado TLS | do IFRN ou Let's Encrypt (certbot) |
| Git | para baixar e atualizar o código |
| Disco | pouco para o sistema; reservar espaço para `media/` (documentos de até 10 MB cada) e `backups/` |
| Rede | saída para `cdnjs.cloudflare.com` e `fonts.googleapis.com` **nos navegadores dos usuários** (ícones e fontes); o servidor não precisa |

Não é preciso Node, npm nem compilar CSS no servidor: o CSS do Tailwind já vem
compilado no repositório (`static/css/tailwind.css`).

---

## 2. Instalação

```bash
# Usuário de sistema sem login
sudo adduser --system --group --home /srv/potimaker potimaker

# Código
sudo -u potimaker git clone <URL-DO-REPOSITORIO> /srv/potimaker/app
cd /srv/potimaker/app

# Ambiente virtual e dependências
sudo -u potimaker python3 -m venv /srv/potimaker/venv
sudo -u potimaker /srv/potimaker/venv/bin/pip install -r requirements.txt
```

---

## 3. Variáveis de ambiente

As configurações sensíveis ficam fora do código, num arquivo lido pelo systemd.
**Não** use o arquivo `.env` do projeto em produção.

```bash
sudo mkdir -p /etc/potimaker
sudo touch /etc/potimaker/potimaker.env
sudo chown root:potimaker /etc/potimaker/potimaker.env
sudo chmod 640 /etc/potimaker/potimaker.env
sudo nano /etc/potimaker/potimaker.env
```

Conteúdo (sem aspas, uma variável por linha):

```ini
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=<cole aqui a chave gerada abaixo>
DJANGO_ALLOWED_HOSTS=potimaker.exemplo.ifrn.edu.br
DJANGO_CSRF_TRUSTED_ORIGINS=https://potimaker.exemplo.ifrn.edu.br
DJANGO_CONFIAR_X_REAL_IP=True
DJANGO_SECURE_HSTS_SECONDS=0
```

| Variável | Obrigatória | Para que serve |
|---|:---:|---|
| `DJANGO_DEBUG` | sim | Tem que ser `False` em produção. Com `True`, qualquer erro exibe código e configurações. |
| `DJANGO_SECRET_KEY` | sim | Assina sessões e tokens. Sem ela (com `DEBUG=False`) o sistema **se recusa a iniciar**. Não reutilize a chave de outro sistema e não a coloque no git. |
| `DJANGO_ALLOWED_HOSTS` | sim | Domínios aceitos, separados por vírgula. |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | sim | Os mesmos domínios **com `https://`**. Sem isso, todos os formulários dão erro 403. |
| `DJANGO_CONFIAR_X_REAL_IP` | sim, atrás do nginx | Faz o sistema ler o IP real do cabeçalho `X-Real-IP` definido pelo nginx. É o que permite bloquear força bruta por IP. **Só é seguro se o gunicorn escutar apenas em 127.0.0.1** (como na seção 5); se o gunicorn ficasse exposto, qualquer um inventaria o próprio IP. |
| `DJANGO_SECURE_HSTS_SECONDS` | não (padrão `0`) | Liga o HSTS. Veja a seção 9 antes de mudar. |
| `DJANGO_SECURE_SSL_REDIRECT` | não (padrão `True`) | Redireciona `http://` para `https://` no Django. Pode ficar `True` mesmo com o nginx também redirecionando. |

Gerar a `SECRET_KEY`:

```bash
/srv/potimaker/venv/bin/python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Os comandos `manage.py` precisam dessas variáveis e do usuário `potimaker`.
Para não repetir isso a cada comando, crie um atalho:

```bash
sudo tee /usr/local/bin/potimaker-manage >/dev/null <<'EOF'
#!/bin/bash
# Roda "python manage.py ..." do PotiMaker como o usuário potimaker, com as variáveis de produção
cd /srv/potimaker/app || exit 1
exec sudo -u potimaker bash -c 'set -a; . /etc/potimaker/potimaker.env; set +a; exec /srv/potimaker/venv/bin/python manage.py "$@"' _ "$@"
EOF
sudo chmod 755 /usr/local/bin/potimaker-manage
```

Daqui em diante, `sudo potimaker-manage <comando>` equivale a
`python manage.py <comando>` no ambiente de produção.

---

## 4. Banco, arquivos estáticos e verificação

```bash
sudo potimaker-manage migrate            # cria/atualiza as tabelas do banco (db.sqlite3)
sudo potimaker-manage collectstatic --noinput   # junta CSS/JS em staticfiles/ (com hash no nome)
sudo potimaker-manage check --deploy     # verificação de segurança do Django
```

Resultado esperado do `check --deploy`: **apenas** o aviso `security.W004`
(HSTS desligado, de propósito — seção 9). Qualquer outro aviso indica variável
de ambiente faltando ou errada.

Permissões (o banco e os backups contêm os hashes das senhas):

```bash
cd /srv/potimaker/app
sudo -u potimaker mkdir -p media backups cache
sudo chmod 750 /srv/potimaker/app
sudo chmod 600 db.sqlite3
sudo chmod 700 backups cache
```

O SQLite cria arquivos temporários ao lado do `db.sqlite3`, então o usuário
`potimaker` precisa poder **escrever na pasta** `/srv/potimaker/app`.

---

## 5. Serviço do gunicorn (systemd)

`/etc/systemd/system/potimaker.service`:

```ini
[Unit]
Description=PotiMaker (gunicorn)
After=network.target

[Service]
Type=simple
User=potimaker
Group=potimaker
WorkingDirectory=/srv/potimaker/app
EnvironmentFile=/etc/potimaker/potimaker.env
# Só 127.0.0.1: o gunicorn não pode ser acessado de fora, apenas pelo nginx.
# 3 workers é suficiente para o laboratório; com SQLite, mais workers não
# aumentam a vazão de escrita.
ExecStart=/srv/potimaker/venv/bin/gunicorn SistemaPotiMaker.wsgi:application \
    --bind 127.0.0.1:8000 \
    --workers 3 \
    --timeout 60 \
    --access-logfile - \
    --error-logfile -
Restart=on-failure
RestartSec=5

# Endurecimento básico
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
ProtectHome=true

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now potimaker
sudo systemctl status potimaker
journalctl -u potimaker -f        # logs
```

---

## 6. nginx com HTTPS

`/etc/nginx/sites-available/potimaker`:

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name potimaker.exemplo.ifrn.edu.br;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    listen [::]:443 ssl;
    # HTTP/2 (opcional): "http2 on;" no nginx 1.25.1 ou mais novo;
    # em versões anteriores (ex.: Debian 12), use "listen 443 ssl http2;".
    server_name potimaker.exemplo.ifrn.edu.br;

    ssl_certificate     /etc/ssl/potimaker/fullchain.pem;
    ssl_certificate_key /etc/ssl/potimaker/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;

    # Documentos técnicos aceitam até 10 MB; a folga cobre o resto do formulário.
    client_max_body_size 12m;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host              $host;
        # Sobrescreve o que o cliente mandar: é neste cabeçalho que o sistema
        # confia para bloquear força bruta por IP (DJANGO_CONFIAR_X_REAL_IP).
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        # O Django usa este cabeçalho para saber que o acesso original era HTTPS.
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        proxy_read_timeout 60s;
    }
}
```

> **Importante — não crie `location /media/` apontando para a pasta `media/`.**
> Fotos de alunos e documentos técnicos só podem ser vistos por usuários
> logados, e quem confere o login é o Django. Se o nginx servir a pasta
> direto, qualquer pessoa com o link baixa os arquivos. Também não é preciso
> `location /static/`: o WhiteNoise já serve os estáticos com cache longo.

```bash
sudo ln -s /etc/nginx/sites-available/potimaker /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

Com Let's Encrypt, o `certbot --nginx -d potimaker.exemplo.ifrn.edu.br` preenche
as linhas `ssl_certificate` automaticamente.

---

## 7. Primeiro coordenador

O sistema tem dois papéis: **coordenador** (aprova cadastros, gerencia membros,
edita a escala, exclui registros) e **membro**. Novos usuários se cadastram
sozinhos em `/usuarios/cadastro/` e ficam pendentes até um coordenador aprovar
— por isso o primeiro coordenador precisa ser criado pelo terminal.

```bash
sudo potimaker-manage createsuperuser
```

O `createsuperuser` cria um usuário com acesso ao `/admin/`, mas com o papel de
**membro** no sistema e sem matrícula. Para torná-lo coordenador (troque
`NOME` pelo usuário criado e `MATRICULA` pela matrícula real):

```bash
sudo potimaker-manage shell -c "from usuarios.models import Usuario; u = Usuario.objects.get(username='NOME'); u.tipo = Usuario.Tipo.COORDENADOR; u.matricula = 'MATRICULA'; u.first_name = 'Nome Completo'; u.save(); print(u, u.get_tipo_display())"
```

A partir daí, entre no sistema com esse usuário. Os próximos coordenadores podem
ser promovidos pela própria interface (Membros → editar → Tipo: Coordenador).
O sistema não deixa rebaixar, desativar ou excluir o **último** coordenador
ativo.

---

## 8. Backup

### 8.1 Banco de dados

O comando `backup_banco` usa a API de backup do SQLite, que gera uma cópia
consistente **mesmo com o sistema rodando** (copiar o `db.sqlite3` com `cp`
durante uma escrita pode gerar um arquivo corrompido). Cada cópia é verificada
(`PRAGMA integrity_check`) e gravada em `backups/db_AAAA-MM-DD_HH-MM-SS.sqlite3`;
as mais antigas além de `--manter` (padrão 30) são apagadas.

```bash
sudo potimaker-manage backup_banco              # mantém as 30 mais recentes
sudo potimaker-manage backup_banco --manter 60
```

Agendamento diário às 3h no cron do usuário `potimaker`
(`sudo crontab -u potimaker -e`):

```cron
0 3 * * * cd /srv/potimaker/app && set -a && . /etc/potimaker/potimaker.env && set +a && /srv/potimaker/venv/bin/python manage.py backup_banco --manter 30 >> /srv/potimaker/backup.log 2>&1
```

### 8.2 Arquivos enviados (`media/`)

O `backup_banco` copia **só o banco**. As fotos e os documentos técnicos ficam
em `media/` e precisam de backup próprio, por exemplo junto com a rotina de
backup de arquivos do NIC, ou:

```cron
30 3 * * * tar -czf /srv/potimaker/app/backups/media_$(date +\%F).tar.gz -C /srv/potimaker/app media && find /srv/potimaker/app/backups -name 'media_*.tar.gz' -mtime +30 -delete
```

### 8.3 Cópia fora do servidor

Backups no mesmo disco não protegem contra falha do disco ou do servidor.
Inclua a pasta `/srv/potimaker/app/backups/` na rotina de backup externo do NIC.
Os arquivos contêm dados pessoais e hashes de senha: trate-os como sigilosos.

### 8.4 Restaurar

```bash
sudo systemctl stop potimaker
cd /srv/potimaker/app
sudo -u potimaker cp db.sqlite3 db.sqlite3.antes-da-restauracao
sudo -u potimaker cp backups/db_AAAA-MM-DD_HH-MM-SS.sqlite3 db.sqlite3
sudo systemctl start potimaker
```

---

## 9. HSTS (depois que o HTTPS estiver estável)

O HSTS faz o navegador recusar `http://` para o domínio pelo tempo configurado.
Protege contra ataques de rebaixamento de conexão, mas **não tem volta**: se o
certificado vencer ou o HTTPS parar de funcionar, os navegadores que já
visitaram o site não conseguem acessá-lo até o prazo acabar. Por isso vem
desligado (`0`).

Quando o HTTPS estiver funcionando há algumas semanas e a renovação do
certificado estiver automatizada:

1. `DJANGO_SECURE_HSTS_SECONDS=3600` (1 hora) e reinicie o serviço; acompanhe.
2. Depois de alguns dias sem problema, `31536000` (1 ano).

Com o HSTS ligado, o `W004` some e o `check --deploy` passa a mostrar
`security.W005` e `security.W021`, que sugerem `SECURE_HSTS_INCLUDE_SUBDOMAINS` e
`SECURE_HSTS_PRELOAD`. **Esses dois avisos são esperados**: as duas opções
afetam outros subdomínios e não devem ser ligadas pelo PotiMaker (o sistema
nem tem variável para elas).

---

## 10. Atualizar o sistema

```bash
cd /srv/potimaker/app
sudo potimaker-manage backup_banco
sudo -u potimaker git pull
sudo -u potimaker /srv/potimaker/venv/bin/pip install -r requirements.txt
sudo potimaker-manage migrate
sudo potimaker-manage collectstatic --noinput
sudo systemctl restart potimaker
sudo potimaker-manage check --deploy
```

---

## 11. Operação do dia a dia

| Situação | Comando |
|---|---|
| Ver logs | `journalctl -u potimaker -f` |
| Usuário bloqueado por errar a senha 5 vezes (libera sozinho em 15 min) | `sudo potimaker-manage axes_reset_username <usuario>` |
| Liberar todos os bloqueios | `sudo potimaker-manage axes_reset` |
| Listar tentativas de login | `sudo potimaker-manage axes_list_attempts` ou `/admin/` → Axes |
| Backup manual | `sudo potimaker-manage backup_banco` |

---

## 12. Conferência após implantar

- [ ] `sudo potimaker-manage check --deploy` mostra só o `security.W004`.
- [ ] `http://potimaker...` redireciona para `https://`.
- [ ] A tela de login abre com o visual completo (cores, ícones, fontes).
- [ ] Login do coordenador funciona; o dashboard carrega.
- [ ] Sem login, abrir `https://potimaker.../media/perfis/<qualquer>.jpg` leva à tela de login.
- [ ] Anexar um PDF numa atividade funciona; anexar um `.html` é recusado.
- [ ] Errar a senha 5 vezes mostra a mensagem de bloqueio; `sudo potimaker-manage axes_reset_username` libera.
- [ ] `sudo potimaker-manage backup_banco` cria um arquivo em `backups/`; o cron está agendado.
- [ ] `sudo ss -tlnp | grep 8000` mostra o gunicorn só em `127.0.0.1`.
