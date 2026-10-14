# PotiMaker

Sistema de gestão do FabLab do IFRN Campus Canguaretama: inventário, projetos (Kanban), membros, agenda e escala de horários.

## Requisitos

- Python 3.12 ou mais recente

## Como rodar

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.exemplo .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

No Linux/macOS, use `source venv/bin/activate` e `cp .env.exemplo .env`.

Acesse http://127.0.0.1:8000 e entre com o usuário criado no `createsuperuser` (ele já é coordenador).

## Testes

```powershell
python manage.py test
```

## Produção

O passo a passo para instalar em servidor (gunicorn, nginx, HTTPS e backup) está em [docs/IMPLANTACAO.md](docs/IMPLANTACAO.md).
