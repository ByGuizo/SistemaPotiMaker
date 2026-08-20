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

# limpar o banco (DESTRUTIVO — sem --sim é só simulação, não apaga nada)
python manage.py limpar_banco
python manage.py limpar_banco --sim

# rodar
python manage.py runserver
```

Não há suíte de testes configurada (os `tests.py` de cada app estão vazios) nem linter/formatter configurado no projeto.

### Estado do banco: começa vazio

O banco é distribuído **limpo** — sem inventário, projetos, atividades, eventos, escala ou presenças, e com apenas os usuários coordenadores `admin` e `byguizo`. Não existe mais o comando `seed_demo` (removido): não recriar dados de exemplo nem repovoar o banco sem o usuário pedir. Membros novos entram pelo auto-cadastro em `/usuarios/cadastro/` e passam por aprovação (ver seção de auto-cadastro abaixo).

`core.management.commands.limpar_banco` reesvazia tudo quando necessário:

- Sem `--sim` faz **dry run**: lista o que seria apagado e sai sem tocar no banco.
- Com `--sim` apaga de verdade, dentro de uma `transaction.atomic()`.
- Preserva os usernames de `USUARIOS_PADRAO` (`admin`, `byguizo`); `--manter user1 user2` sobrescreve essa lista. Se algum username a preservar não existir, o comando aborta sem apagar nada — evita esvaziar o banco e ficar sem acesso.

## Architecture

### Apps e suas responsabilidades

- **`SistemaPotiMaker/`** — pacote de configuração Django (settings, urls raiz, wsgi/asgi). Não é um app.
- **`core/`** — não tem models próprios. Agrega dados de todos os outros apps para o dashboard (`core/views.py`), define a template tag `badge` (`core/templatetags/potimaker_tags.py`) usada em todos os apps, o mixin de estilo de formulário e o `CampoMembrosWidget` (`core/forms.py`), e o comando `limpar_banco`.
- **`usuarios/`** — model de usuário customizado (`AUTH_USER_MODEL = 'usuarios.Usuario'`), autenticação, o middleware que exige login global, a escala de horários do laboratório e o perfil de usuário.
- **`inventario/`**, **`projetos/`**, **`agenda/`** — um domínio cada (itens, projetos/atividades em Kanban, calendário/eventos), seguindo todos o mesmo padrão de app (veja abaixo).

### Padrão de app de domínio

Cada app de domínio (`inventario`, `projetos`, `agenda`, `usuarios`) segue a mesma estrutura: `models.py`, `forms.py`, `views.py`, `urls.py` com `app_name`, e templates em `<app>/templates/<app>/`. Ao adicionar um novo domínio, replicar esse padrão em vez de inventar um novo.

### Views que servem HTMX e página completa da mesma função

Views de listagem (inventário, Kanban, membros) checam o header `HX-Request` e escolhem entre o partial (fragmento) ou o template completo que estende `base.html`:

```python
template = 'app/partials/_algo.html' if request.headers.get('HX-Request') else 'app/pagina.html'
return render(request, template, contexto)
```

O partial e a página completa recebem o mesmo contexto — o partial é incluído dentro da página completa via `{% include %}`. Ver `inventario/views.py:lista_itens` ou `projetos/views.py:kanban` como referência.

### Projetos e Atividades (`projetos.models`)

O Kanban não move `Projeto` — move `Atividade`. `Projeto` é só um agrupador (`nome` + `descricao`); todo campo que aparece no card (status, prioridade, prazo, membros, documento técnico) pertence a `Atividade`, que tem FK obrigatória para `Projeto` (`related_name='atividades'`). Ao adicionar campo novo ao card do Kanban, adicionar em `Atividade`, não em `Projeto`.

- `projetos.views.kanban` filtra por `?projeto=<id>` (dropdown com HTMX, mesmo padrão de filtro do inventário) — sem esse parâmetro, mostra atividades de todos os projetos juntas.
- `Projeto.em_andamento` (property) — `True` se o projeto tem ao menos uma atividade em `A_FAZER` ou `FAZENDO`. Usado para contar "projetos em andamento" no dashboard (`core/views.py`) e para o badge da listagem de projetos (`projetos/templates/projetos/lista_projetos.html`). Não confundir com o status da atividade individual.
- "Meus projetos" no perfil (`usuarios/templates/usuarios/perfil.html`) é derivado de `Projeto.objects.filter(atividades__membros=usuario).distinct()` — não existe mais FK/M2M direta entre `Usuario` e `Projeto`.
- Duas telas distintas: `/projetos/` (Kanban de atividades) e `/projetos/lista/` (CRUD de projetos-container). Rotas de atividade vivem sob `/projetos/atividades/...`.

### Permissões

Duas camadas, não uma só:

1. **`usuarios.middleware.LoginObrigatorioMiddleware`** (em `MIDDLEWARE`) — exige login em toda a aplicação, exceto `/usuarios/login/`, `/admin/` e arquivos estáticos/media (lista em `CAMINHOS_PUBLICOS`). Não há área pública.
2. **`usuarios.decorators.coordenador_required`** — restringe uma view a usuários com `tipo == COORDENADOR` (via `Usuario.is_coordenador`). Usado especificamente em ações de exclusão e gestão de membros.

Regra vigente: qualquer usuário logado pode cadastrar/editar itens, projetos, atividades e eventos, e mover cards do Kanban. Só coordenador exclui registros, edita membros e aprova/nega cadastros. Ao adicionar uma view de escrita, decidir explicitamente entre `@login_required` (ação de membro comum) e `@coordenador_required` (ação restrita) — não usar um decorator genérico "de segurança" sem pensar em qual dos dois papéis a ação pertence.

### Auto-cadastro com aprovação (`usuarios`)

Não existe mais criação de membro pelo coordenador (`novo_membro` e a rota `/usuarios/membros/novo/` foram removidas). O fluxo é: o visitante se cadastra sozinho em `/usuarios/cadastro/` (rota pública, listada em `CAMINHOS_PUBLICOS` do middleware) informando só **nome, usuário, matrícula e senha** — o model tem `email` herdado do `AbstractUser`, mas nenhum formulário do sistema o coleta; não reintroduzir campo de e-mail nesses formulários.

- `Usuario.status_cadastro` (`PENDENTE`/`APROVADO`, default `APROVADO`) é a fonte da verdade do fluxo de aprovação. O default é `APROVADO` de propósito, para que usuários criados pelo admin/`createsuperuser` já nasçam válidos — só o `CadastroForm` cria como `PENDENTE`.
- Não confundir com `is_active`: pendente tem os dois (`status_cadastro=PENDENTE` e `is_active=False`, que é o que efetivamente bloqueia o login no backend do Django). `is_active` continua significando "membro ativo do laboratório" nas queries de escala/dashboard, então **não** reutilizar `is_active` sozinho para representar "aguardando aprovação".
- `Usuario.aprovar(coordenador)` é o único caminho de aprovação — marca `APROVADO`, reativa e registra `aprovado_por`/`aprovado_em`. Negar (`usuarios.views.negar_cadastro`) **exclui** o usuário, conforme a regra do fluxo.
- O painel "Cadastros pendentes" aparece no topo do dashboard só para coordenador (`core/templates/core/partials/_cadastros_pendentes.html`); `core.views.dashboard` só popula `cadastros_pendentes` nesse caso.
- `LoginForm.get_invalid_login_error()` diferencia "aguardando aprovação" de "senha errada". A checagem acontece ali (e não em `confirm_login_allowed`) porque o pendente tem `is_active=False` e o `ModelBackend` o rejeita antes. A mensagem só aparece quando a senha confere — manter essa condição, senão vira enumeração de usuários.
- `usuarios.views.lista_membros` filtra por `status_cadastro=APROVADO`: pendentes não são "membros" e não devem aparecer na listagem nem na escala.

### Badges e template tag `badge`

Cores e ícones de badges (status de item, categoria, prioridade, tipo de usuário) são centralizados em `core/templatetags/potimaker_tags.py` nos dicionários `CORES_*`/`ICONES_*` e no mapa `MAPAS`/`ICONES`. Para renderizar: `{% badge valor "nome_do_mapa" rotulo_opcional %}`, que usa `templates/partials/_badge.html`. Ao adicionar um novo `TextChoices` que precisa de badge visual, adicionar as entradas nesses dicionários em vez de estilizar inline no template.

### Escala de horários (`usuarios.models.HorarioEscala`)

Grade fixa semanal (5 dias úteis × 6 slots fixos `M1..M3`/`T1..T3`, com horários hardcoded em `HorarioEscala.HORARIOS`) que representa quem deve estar no laboratório em cada horário. Não é uma agenda de eventos avulsos (isso é o app `agenda`) — é o cronograma recorrente da equipe gestora.

- `usuarios.services.escala_atual()` — alimenta o card "Quem deve estar agora" no dashboard. Retorna **um dict** `{'horario': HorarioEscala, 'em_andamento': bool}`, ou `None` em fim de semana e após o último slot do dia. Os 6 slots **não cobrem o dia inteiro** (há ~2h de intervalos, incluindo o almoço): quando a hora atual cai num intervalo, `em_andamento=False` e `horario` é o **próximo** slot do dia — antes disso a função retornava `None` nesses buracos e o painel sumia em ~14% do expediente mesmo com a escala preenchida. O template `core/partials/_escala_atual.html` usa `escala.horario.membros.all` e troca o rótulo conforme `escala.em_andamento`; ao mexer na função, manter as duas chaves.
- `usuarios.services.grade_horarios()` — monta a matriz completa (linhas = slots, colunas = dias) para a tela de edição.
- Edição em massa: `usuarios.views.editar_horarios` (só coordenador) recebe um POST com campos `celula_{dia_semana}_{slot}` (cada um uma lista de IDs de membro) e faz `get_or_create` + `membros.set(...)` por célula. Ao mexer nessa view ou no template `usuarios/templates/usuarios/editar_horarios.html`, manter a convenção de nome de campo `celula_<dia>_<slot>` sincronizada entre os dois lados.

### Widget de campo de membros (`static/js/multi-select.js`)

Componente vanilla JS (classe `CampoMembros`) que substitui o `<select multiple>` nativo (que exigia segurar Ctrl). O campo é **um input de texto**, não uma lista de seleção: digita-se o nome, ele completa inline (o trecho completado fica selecionado, como na barra de endereço), e Enter/Tab confirma virando um chip. Usado nas células da escala de horários. Não há build step — é um IIFE carregado via `{% block scripts %}`, com estilos em `custom.css` sob o prefixo `.ms-*`.

O autocomplete inline substitui o texto digitado pelo **nome canônico inteiro** (`this.entrada.value = alvo`), não pelo digitado + resto — assim "jos" vira "Josué Costa" com maiúsculas e acentos corretos. Não completar quando `inputType` começa com `delete`, senão o Backspace trava.

**Em formulário Django, use o widget `core.forms.CampoMembrosWidget`** — não escreva o markup à mão. Ele já gera o JSON, o `<noscript>` e declara o JS em `Media`:

```python
widgets = {'membros': CampoMembrosWidget}
```

Para o JS chegar na página, o template do formulário precisa de `{{ form.media }}` (já está em `templates/form_generico.html`, no `{% block scripts %}`). Aplicado em `projetos.forms.AtividadeForm`; a escala de horários usa o markup manual porque a grade não é um `ModelForm`.

Markup esperado (o JS monta o resto):

```html
<div class="multi-select" data-nome="celula_0_M1" data-placeholder="...">
    <script type="application/json" class="multi-select-dados">
        [{"id": "1", "texto": "Ana Pimentel", "selecionado": true}]
    </script>
</div>
```

- Emite `<input type="hidden" name="{data-nome}">` por item selecionado — **mesmo formato do `select multiple`**, então views existentes não precisam mudar. Ao reusar o widget em outro formulário, basta que a view leia com `request.POST.getlist(nome)`.
- Sempre acompanhar de um `<noscript>` com o `<select multiple>` equivalente; o CSS `.multi-select:not(.ms-raiz) { display: none }` esconde a div vazia quando o JS não roda (a classe `.ms-raiz` só é adicionada na montagem).
- O painel é `position: fixed` com coordenadas calculadas em `posicionarPainel()`, porque a tabela da escala vive dentro de um `overflow-x-auto` que recortaria um painel absoluto. Se mudar o layout da tabela, conferir se o painel ainda escapa do container.
- Busca ignora acentos nos dois sentidos ("josue" acha "Josué"); resultados que *começam* com o termo vêm primeiro, pois é o que Enter/Tab completa. Quem já foi adicionado sai das sugestões (não há como duplicar).
- No chip, avatar e nome são elementos separados (`.ms-chip-avatar` + `.ms-chip-nome`, com `padding` próprio) — sem isso a inicial cola no nome e vira "LLuiz Miguel".

### Modo escuro (`static/js/tema.js` + bloco "MODO ESCURO" em `custom.css`)

O tema vive no atributo `data-tema="escuro"` do `<html>` e é persistido em `localStorage` sob a chave `potimaker-tema`. O botão (lua/sol) fica no header de `base.html` com a classe `.btn-tema` — o JS liga o clique em **todos** os elementos com essa classe, então dá para ter mais de um.

- **`tema.js` é carregado de forma síncrona no `<head>`, antes do `<body>`** (em `base.html`, `login.html` e `cadastro.html`). Isso é intencional: se fosse `defer` ou ficasse no fim da página, o usuário veria um flash branco antes do tema escuro ser aplicado. Não mover para `{% block scripts %}`.
- Sem escolha salva, segue o `prefers-color-scheme` do sistema — e continua seguindo até o usuário clicar no botão pela primeira vez.
- Todo acesso ao `localStorage` está em `try/catch`: em modo privado ele pode lançar exceção, e o tema precisa continuar funcionando (só sem persistir).
- Os templates usam utilitários Tailwind fixos (`bg-white`, `text-black`, `border-black`...). O tema escuro **não** reescreve os templates: inverte essas classes no CSS sob `[data-tema="escuro"]`, com `!important` para vencer a especificidade do Tailwind. Ao criar tela nova, usar as classes já existentes (`bg-white` para superfície, `text-gray-500` para texto secundário) que o modo escuro pega de graça — se introduzir uma classe de superfície nova (ex: `bg-slate-50`), adicionar o override no bloco "MODO ESCURO".
- As cores de marca (fúcsia, amarelo, esmeralda, roxo, ciano) **não** mudam no escuro — são a identidade visual e contrastam bem. O que muda é o texto sobre elas, que vira escuro.

### Comentários em template Django

`{# ... #}` só funciona em **uma linha**. Se abrir numa linha e fechar em outra, o Django não reconhece como comentário e **imprime o texto na página** (já aconteceu no header de `base.html`). Para comentário de várias linhas usar `{% comment %}...{% endcomment %}`, ou quebrar em vários `{# #}` de uma linha cada.

### Cache de estáticos em desenvolvimento

`custom.css` e os JS são servidos sem hash de versão, então o navegador segura versões antigas com força e mudanças de CSS parecem "não ter efeito". Os `<link>`/`<script>` desses arquivos carregam `?v=N` manual (em `templates/base.html`, `usuarios/login.html`, `usuarios/cadastro.html` e `usuarios/editar_horarios.html`; o JS do campo de membros também em `core.forms.CampoMembrosWidget.Media`). **Ao alterar `custom.css` ou um JS de `static/`, incrementar o `?v=` em todos os pontos** — senão o usuário continua vendo o arquivo antigo.

### Status do laboratório vs. escala de horários — não confundir

`usuarios.services.status_laboratorio()` deriva "aberto/fechado" e contagem de presença a partir de `RegistroPresenca` (histórico de entradas registradas). Isso é independente da `HorarioEscala` (cronograma planejado) — um mostra o que *deveria* acontecer, o outro o que *de fato* aconteceu; não fundir a lógica dos dois. O painel "Status do laboratório" foi removido do dashboard, então `status_laboratorio()` hoje não tem consumidor — continua disponível como serviço. Não existe mais view para o usuário registrar a própria presença (`registrar_presenca` foi removida) — `RegistroPresenca` hoje só é populado via admin do Django.

### Dashboard (`core/views.py` + `core/templates/core/dashboard.html`)

Os 4 cards de contagem no topo são também os links de navegação para cada domínio (membros, projetos, inventário, agenda) — não existe mais um bloco "Acesso rápido" separado, que duplicava esses mesmos 4 destinos. Ao adicionar um atalho novo, considerar primeiro se ele cabe como card de contagem em vez de criar uma segunda lista de links. Abaixo dos cards, o dashboard mostra painéis alimentados por dados reais: "Minhas atividades" (atividades em aberto do usuário logado), "Quem deve estar agora" (escala), "Atividades atrasadas" (`prazo` menor que hoje), "Próximos eventos" e "Itens em manutenção" — todos limitados a poucos registros via slice na view.

### Layout base e rodapé fixo

`templates/base.html` é a única base compartilhada por todos os apps (`{% extends "base.html" %}` + `{% block content %}`). O rodapé fica sempre fixado ao final da página, mesmo em telas com pouco conteúdo, via Flexbox: `body` é `flex flex-col min-h-screen`, `main` é `flex-1 w-full`, `footer` é `shrink-0`. Não recriar essa estrutura em templates individuais — qualquer página nova deve estender `base.html` normalmente e essa regra já se aplica.

### Fuso horário

`TIME_ZONE = 'America/Recife'` e `USE_TZ = True` no settings. Qualquer cálculo de "agora" (escala atual, presença do dia) deve usar `django.utils.timezone.localtime()`/`localdate()`, nunca `datetime.now()`.

### Variáveis de ambiente em produção

`SECRET_KEY`, `DEBUG` e `ALLOWED_HOSTS` já leem de `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS` com fallback de desenvolvimento em `SistemaPotiMaker/settings.py`. Banco continua SQLite (migração para Postgres é item pendente do roadmap no README).
