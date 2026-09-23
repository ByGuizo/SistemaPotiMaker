# FabLab PotiMaker — Sistema de Gerenciamento

Sistema web de gestão para o **Laboratório de Inovação e Prototipagem (FabLab) do IFRN Campus Canguaretama**. Centraliza o controle de inventário, projetos, membros, agenda de eventos e a escala de horários do laboratório em um só lugar, com uma identidade visual própria (estilo neo-brutalista, cores vibrantes e animações lúdicas).

> "Faça você mesmo, seja um maker."

---

## Sumário

- [Visão geral](#visão-geral)
- [Funcionalidades](#funcionalidades)
- [Stack técnica](#stack-técnica)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Modelo de permissões](#modelo-de-permissões)
- [Como rodar localmente](#como-rodar-localmente)
- [Estado inicial do banco](#estado-inicial-do-banco)
- [Identidade visual](#identidade-visual)
- [Roadmap / próximos passos](#roadmap--próximos-passos)

---

## Visão geral

O PotiMaker é um sistema Django multi-app pensado para o dia a dia de um laboratório maker escolar: quem está presente, o que tem no inventário, em que pé estão os projetos, quando são os próximos eventos. O acesso é restrito a membros cadastrados — não há área pública, exceto a tela de login.

Existem dois papéis de usuário:

- **Coordenador** — acesso total, incluindo exclusão de itens/projetos/eventos/membros, cadastro de novos membros e edição da escala de horários do laboratório.
- **Membro** — pode navegar por todas as telas, cadastrar e editar itens de inventário, projetos e eventos da agenda. Não pode excluir registros, gerenciar outros membros nem editar a escala de horários.

---

## Funcionalidades

### Dashboard
Painel inicial com contadores (membros ativos, projetos em andamento, itens no inventário, eventos da semana), atalhos de acesso rápido, o card "Quem deve estar agora" (com base na escala de horários) e o status do laboratório (aberto/fechado, membros com entrada registrada no dia, próximo evento) — tudo atualizado via HTMX sem recarregar a página.

### Inventário
Cadastro de itens (equipamentos, ferramentas, consumíveis, componentes eletrônicos) com categoria, quantidade e status (disponível / em uso / em manutenção). Busca e filtros em tempo real.

### Projetos e Atividades (Kanban)
Cada **Projeto** agrupa uma ou mais **Atividades** — é a atividade que aparece como card no Kanban, com três colunas (*A Fazer*, *Fazendo*, *Concluído*), prioridade, prazo, descrição, membros responsáveis e documento técnico anexável. Mover um card entre colunas é feito com um clique, via HTMX. A tela do Kanban tem um filtro por projeto (dropdown), e uma tela separada lista os projetos cadastrados com a contagem de atividades de cada um.

### Membros
Listagem e cadastro de membros do laboratório, com busca por nome/e-mail e filtro por tipo (coordenador/membro). Apenas coordenadores podem criar, editar ou excluir membros.

### Agenda
Calendário mensal nativo (implementado com o módulo `calendar` do Python, sem dependência de bibliotecas de calendário em JS), com navegação entre meses e painel lateral de eventos do dia selecionado.

### Perfil do usuário
Cada usuário logado pode acessar seu próprio perfil (clicando no nome no canto superior do header) para ver seus dados, os projetos em que está envolvido e seu histórico de entradas registradas.

### Escala de horários
Grade fixa semanal (5 dias úteis × 6 horários, replicando o cronograma da equipe gestora do laboratório) que define quem deve estar presente em cada horário. O dashboard mostra automaticamente quem está escalado para o momento atual no card "Quem deve estar agora". Apenas coordenadores podem editar a escala completa, atribuindo um ou mais membros a cada célula da grade.

### Status do laboratório
Card independente da escala de horários: deriva "aberto/fechado" e a contagem de membros com entrada registrada no dia a partir do histórico real de presença (`RegistroPresenca`) — mostra o que *de fato* aconteceu, enquanto a escala de horários mostra o que *deveria* acontecer.

---

## Stack técnica

| Camada | Tecnologia |
|---|---|
| Backend | Django 6.0 (Python) |
| Banco de dados (dev) | SQLite |
| Frontend | Django Templates + Tailwind CSS 3.4 (compilado pelo CLI standalone) |
| Interatividade | HTMX (fragmentos de HTML renderizados no servidor, sem SPA) |
| Ícones | Font Awesome 6 |
| Tipografia | Space Grotesk (títulos) + Manrope (corpo), via Google Fonts |

Não há Node, npm, Webpack nem Vite. O único passo de build é o Tailwind, gerado por um executável standalone (veja [Regenerar o CSS do Tailwind](#regenerar-o-css-do-tailwind)); o CSS compilado (`static/css/tailwind.css`) fica versionado no git, então para só rodar o sistema não é preciso compilar nada. HTMX é servido de `static/`; Font Awesome e as fontes vêm de CDN.

---

## Estrutura do projeto

```
SistemaPotiMaker/        # pacote de configuração Django (settings, urls, wsgi/asgi)
core/                    # dashboard agregador, template tags de badges, comando limpar_banco
usuarios/                # model de usuário customizado, autenticação, presença, perfil
inventario/              # modelo e views de itens do inventário
projetos/                # modelos Projeto/Atividade e views do Kanban
agenda/                  # modelo e views do calendário/eventos
templates/               # base.html e partials compartilhados entre apps
static/                  # CSS customizado, Tailwind compilado, JS e HTMX local
tailwind.config.js       # configuração do Tailwind (cores, sombras, animações)
```

Cada app de domínio (`usuarios`, `inventario`, `projetos`, `agenda`) segue o mesmo padrão: `models.py`, `forms.py`, `views.py`, `urls.py`, e templates próprios em `app/templates/app/`. Views que respondem a requisições HTMX retornam apenas o fragmento HTML relevante; requisições normais recebem a página completa estendendo `base.html`.

---

## Modelo de permissões

A autenticação é obrigatória em todo o sistema (via `usuarios.middleware.LoginObrigatorioMiddleware`), exceto na tela de login e no admin do Django.

| Ação | Membro | Coordenador |
|---|:---:|:---:|
| Visualizar dashboard, inventário, projetos, membros, agenda | ✅ | ✅ |
| Cadastrar/editar itens do inventário | ✅ | ✅ |
| Cadastrar/editar projetos e atividades | ✅ | ✅ |
| Cadastrar/editar eventos da agenda | ✅ | ✅ |
| Mover atividades no Kanban | ✅ | ✅ |
| Ver e editar o próprio perfil | ✅ | ✅ |
| Excluir itens, projetos, atividades ou eventos | ❌ | ✅ |
| Cadastrar, editar ou excluir membros | ❌ | ✅ |
| Editar a escala de horários do laboratório | ❌ | ✅ |

---

## Como rodar localmente

Pré-requisitos: Python 3.12+ (exigência do Django 6.0) e um ambiente virtual.

```powershell
# 1. Criar e ativar o ambiente virtual
python -m venv venv
venv\Scripts\activate

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Criar a configuração local (liga o modo de desenvolvimento)
copy .env.exemplo .env

# 4. Aplicar as migrations
python manage.py migrate

# 5. Criar um superusuário (acesso ao /admin/)
python manage.py createsuperuser

# 6. Rodar o servidor de desenvolvimento
python manage.py runserver
```

Sem o arquivo `.env`, o sistema entende que está em **produção** (`DEBUG` desligado)
e se recusa a iniciar sem uma `DJANGO_SECRET_KEY`. Isso é proposital — veja
`docs/NOTAS_DE_CORRECOES.md`. Para colocar em um servidor, siga `docs/IMPLANTACAO.md`.

Acesse `http://127.0.0.1:8000/`. Todo o sistema exige login — use o superusuário criado.

### Regenerar o CSS do Tailwind

O `static/css/tailwind.css` contém só as classes que os templates usam. **Depois de
usar uma classe do Tailwind que ainda não aparecia em nenhum template** (ou de mexer
no `tailwind.config.js`), é preciso regenerá-lo — senão a classe nova não tem efeito.

1. Baixe o executável **uma vez** — Tailwind CLI standalone **v3.4.x** (não use a 4.x,
   que tem outro formato de configuração), do release oficial em
   <https://github.com/tailwindlabs/tailwindcss/releases/tag/v3.4.19>:
   `tailwindcss-windows-x64.exe` no Windows ou `tailwindcss-linux-x64` no Linux.
   Salve na raiz do projeto como `tailwindcss.exe` (Windows) ou `tailwindcss-linux-x64`
   (Linux, com `chmod +x`). Esses arquivos estão no `.gitignore`.
2. Gere o CSS:

   ```powershell
   .\tailwindcss.exe -i tailwind-entrada.css -o static/css/tailwind.css --minify
   ```

   Durante o desenvolvimento, `--watch` no lugar de `--minify` regera a cada alteração.
3. Incremente o `?v=` do `tailwind.css` em `templates/base.html`,
   `usuarios/templates/usuarios/login.html` e `usuarios/templates/usuarios/cadastro.html`.
4. Faça commit do `static/css/tailwind.css` junto com o template alterado.

O `content` do `tailwind.config.js` inclui, além dos templates, `core/templatetags/*.py`
e `core/forms.py`, porque as cores dos badges e o estilo dos campos são montados em
Python. Classes montadas por concatenação (ex.: `"bg-" + cor`) **não** são detectadas:
escreva sempre o nome inteiro da classe.

---

## Estado inicial do banco

O sistema começa **vazio**: sem itens de inventário, projetos, atividades, eventos, escala de horários ou registros de presença. Os únicos usuários são os coordenadores `admin` e `byguizo`.

A partir daí, o cadastro é feito pelo próprio sistema: novos membros se cadastram em `/usuarios/cadastro/` (link na tela de login) e ficam pendentes até que um coordenador aprove pelo painel no dashboard. Inventário, projetos e eventos são cadastrados pelas telas correspondentes.

### Limpar o banco

Para voltar ao estado inicial, existe o comando `limpar_banco`:

```powershell
# Simulação: mostra o que seria apagado, sem apagar nada
python manage.py limpar_banco

# Apaga de verdade (preserva os usuários admin e byguizo)
python manage.py limpar_banco --sim

# Preservando outros usuários
python manage.py limpar_banco --sim --manter admin maria.santos
```

⚠️ A operação é **irreversível** — faça uma cópia do `db.sqlite3` antes se houver dados que importam.

---

## Identidade visual

O design segue uma linha **neo-brutalista**: bordas pretas grossas, sombras sólidas ("brutal shadows"), paleta vibrante (roxo, fúcsia, amarelo, verde-água) sobre um fundo bege pontilhado. As interações têm animações expressivas — cards que saltam ao hover, entradas em cascata, badges com pulso sutil — para dar uma sensação mais lúdica e "maker" ao sistema. A tela de login tem um design próprio, independente do restante do sistema, com fundo em gradiente animado e formas flutuantes.

O layout base usa um sticky footer (`body` como flex container em coluna, `main` com `flex-1`): o rodapé fica sempre fixado ao final da página em todas as telas, independentemente da quantidade de conteúdo.

---

## Roadmap / próximos passos

- [ ] Migrar de SQLite para PostgreSQL para uso em produção
- [x] Configurar variáveis de ambiente para `SECRET_KEY` e `DEBUG` (`.env` no desenvolvimento; ver `docs/IMPLANTACAO.md`)
- [ ] Deploy em produção (domínio próprio + HTTPS)
- [x] Backups do banco de dados (`python manage.py backup_banco`; agendamento no cron descrito em `docs/IMPLANTACAO.md`)
