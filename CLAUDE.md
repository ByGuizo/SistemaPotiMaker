# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

PotiMaker — sistema de gestão do FabLab (Laboratório de Inovação e Prototipagem) do IFRN Campus Canguaretama. Django multi-app, sem SPA: Django Templates + Tailwind CSS (CDN) + HTMX para interatividade, Font Awesome para ícones. Sem build step de frontend (nenhum Webpack/Vite/npm) — tudo carregado via CDN ou de `static/`.

Idioma: todo o código (models, views, nomes de variáveis, templates) é em português. Manter esse padrão em código novo.

## Commands

```powershell
# ambiente virtual
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# banco de dados
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser

# dados de exemplo (idempotente — pode rodar de novo sem duplicar; senha sempre potimaker123)
python manage.py seed_demo

# rodar
python manage.py runserver
```

Não há suíte de testes configurada (os `tests.py` de cada app estão vazios) nem linter/formatter configurado no projeto.

## Architecture

### Apps e suas responsabilidades

- **`SistemaPotiMaker/`** — pacote de configuração Django (settings, urls raiz, wsgi/asgi). Não é um app.
- **`core/`** — não tem models próprios. Agrega dados de todos os outros apps para o dashboard (`core/views.py`), define a template tag `badge` (`core/templatetags/potimaker_tags.py`) usada em todos os apps, o mixin de estilo de formulário (`core/forms.py`), e o comando `seed_demo`.
- **`usuarios/`** — model de usuário customizado (`AUTH_USER_MODEL = 'usuarios.Usuario'`), autenticação, o middleware que exige login global, a escala de horários do laboratório e o perfil de usuário.
- **`inventario/`**, **`projetos/`**, **`agenda/`** — um domínio cada (itens, Kanban de projetos, calendário/eventos), seguindo todos o mesmo padrão de app (veja abaixo).

### Padrão de app de domínio

Cada app de domínio (`inventario`, `projetos`, `agenda`, `usuarios`) segue a mesma estrutura: `models.py`, `forms.py`, `views.py`, `urls.py` com `app_name`, e templates em `<app>/templates/<app>/`. Ao adicionar um novo domínio, replicar esse padrão em vez de inventar um novo.

### Views que servem HTMX e página completa da mesma função

Views de listagem (inventário, Kanban, membros) checam o header `HX-Request` e escolhem entre o partial (fragmento) ou o template completo que estende `base.html`:

```python
template = 'app/partials/_algo.html' if request.headers.get('HX-Request') else 'app/pagina.html'
return render(request, template, contexto)
```

O partial e a página completa recebem o mesmo contexto — o partial é incluído dentro da página completa via `{% include %}`. Ver `inventario/views.py:lista_itens` ou `projetos/views.py:kanban` como referência.

### Permissões

Duas camadas, não uma só:

1. **`usuarios.middleware.LoginObrigatorioMiddleware`** (em `MIDDLEWARE`) — exige login em toda a aplicação, exceto `/usuarios/login/`, `/admin/` e arquivos estáticos/media (lista em `CAMINHOS_PUBLICOS`). Não há área pública.
2. **`usuarios.decorators.coordenador_required`** — restringe uma view a usuários com `tipo == COORDENADOR` (via `Usuario.is_coordenador`). Usado especificamente em ações de exclusão e gestão de membros.

Regra vigente: qualquer usuário logado pode cadastrar/editar itens, projetos e eventos, e mover cards do Kanban. Só coordenador exclui registros e gerencia (cria/edita/exclui) outros membros. Ao adicionar uma view de escrita, decidir explicitamente entre `@login_required` (ação de membro comum) e `@coordenador_required` (ação restrita) — não usar um decorator genérico "de segurança" sem pensar em qual dos dois papéis a ação pertence.

### Badges e template tag `badge`

Cores e ícones de badges (status de item, categoria, prioridade, tipo de usuário) são centralizados em `core/templatetags/potimaker_tags.py` nos dicionários `CORES_*`/`ICONES_*` e no mapa `MAPAS`/`ICONES`. Para renderizar: `{% badge valor "nome_do_mapa" rotulo_opcional %}`, que usa `templates/partials/_badge.html`. Ao adicionar um novo `TextChoices` que precisa de badge visual, adicionar as entradas nesses dicionários em vez de estilizar inline no template.

### Escala de horários (`usuarios.models.HorarioEscala`)

Grade fixa semanal (5 dias úteis × 6 slots fixos `M1..M3`/`T1..T3`, com horários hardcoded em `HorarioEscala.HORARIOS`) que representa quem deve estar no laboratório em cada horário. Não é uma agenda de eventos avulsos (isso é o app `agenda`) — é o cronograma recorrente da equipe gestora.

- `usuarios.services.escala_atual()` — calcula o slot correspondente ao dia/hora atual (`timezone.localtime()`) e retorna o `HorarioEscala` com seus membros, ou `None` fora do expediente/fim de semana. Alimenta o card "Quem deve estar agora" no dashboard.
- `usuarios.services.grade_horarios()` — monta a matriz completa (linhas = slots, colunas = dias) para a tela de edição.
- Edição em massa: `usuarios.views.editar_horarios` (só coordenador) recebe um POST com campos `celula_{dia_semana}_{slot}` (cada um uma lista de IDs de membro) e faz `get_or_create` + `membros.set(...)` por célula. Ao mexer nessa view ou no template `usuarios/templates/usuarios/editar_horarios.html`, manter a convenção de nome de campo `celula_<dia>_<slot>` sincronizada entre os dois lados.

### Status do laboratório vs. escala de horários — não confundir

`usuarios.services.status_laboratorio()` deriva "aberto/fechado" e contagem de presença a partir de `RegistroPresenca` (histórico de entradas registradas). Isso é independente da `HorarioEscala` (cronograma planejado) — um mostra o que *deveria* acontecer, o outro o que *de fato* aconteceu. O dashboard mostra os dois cards lado a lado; não fundir a lógica dos dois.

### Fuso horário

`TIME_ZONE = 'America/Recife'` e `USE_TZ = True` no settings. Qualquer cálculo de "agora" (escala atual, presença do dia) deve usar `django.utils.timezone.localtime()`/`localdate()`, nunca `datetime.now()`.

### Variáveis de ambiente em produção

`SECRET_KEY`, `DEBUG` e `ALLOWED_HOSTS` já leem de `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS` com fallback de desenvolvimento em `SistemaPotiMaker/settings.py`. Banco continua SQLite (migração para Postgres é item pendente do roadmap no README).
