# Resumo da Aplicação: `mirim`

A aplicação `mirim` é um sistema completo desenvolvido em Django para gerenciar a "Guarda Mirim". Ela controla o cadastro dos jovens guardas, a criação de eventos (como missas e treinamentos), o registro de frequências (check-in) e a validação de aptidão para o evento anual do Círio, com base em regras de presença.

Abaixo, detalho o funcionamento de cada arquivo e de suas respectivas funções.

---

## 1. Onde está o Front-End?
No Django, o front-end é construído utilizando **Templates** (arquivos HTML que se comunicam com o back-end). 
Para a aplicação `mirim`, os arquivos de front-end não estão dentro da pasta `mirim/`, e sim na pasta global de templates do projeto:
👉 **`C:\Users\Paulo Moraes\GNSN-discentes\templates\mirim\`**

Nessa pasta estão os arquivos HTML como `dashboard.html`, `mirim_list.html`, `checkin.html`, entre outros, que cuidam do visual da aplicação. Alguns templates genéricos, como o `index.html` e a base do site, ficam na raiz da pasta `templates\`.

---

## 2. Arquivos e Funções

### `models.py`
Este arquivo define a estrutura do banco de dados (as tabelas). Cada classe aqui vira uma tabela no banco de dados.
- **`CategoriaEvento`**: Tabela para cadastrar tipos de evento (Ex: Missa, Reunião, Treinamento).
- **`Local`**: Tabela para cadastrar onde os eventos ocorrem.
- **`GuardaMirim`**: Guarda os dados pessoais, médicos e de contato do jovem. Possui lógicas embutidas:
  - `total_presencas()`: Conta as faltas/presenças do guarda.
  - `progresso_percentual()`: Calcula a porcentagem geral de presença.
  - `status_aptidao()`: Define se o guarda está com frequência boa, constante ou baixa baseada em uma meta de 52 presenças anuais.
  - `progresso_por_cirio()` e `status_no_cirio()`: Calculam o progresso específico baseado nas regras de um determinado Círio.
- **`Evento`**: Tabela de eventos agendados, atrelando uma `CategoriaEvento`, um `Local`, data e hora.
- **`Frequencia`**: Tabela que liga um `GuardaMirim` a um `Evento` quando o check-in é realizado.
- **`Cirio`**: Tabela que define o período (data de início e fim) de preparação para um Círio específico.
- **`RegraCirio`**: Define a quantidade mínima de presenças necessárias em cada categoria de evento para que o guarda seja considerado "Apto" para um Círio.

### `forms.py`
Neste arquivo estão os formulários, responsáveis por validar os dados digitados pelo usuário antes de salvar no banco e por gerar o HTML dos campos (inputs).
- **`BootstrapModelForm`**: Uma classe base personalizada que pega todos os campos do formulário e aplica as classes CSS do Bootstrap (ex: `form-control`) automaticamente para deixar o formulário bonito.
- **`CategoriaEventoForm`, `LocalForm`, `GuardaMirimForm`, `EventoForm`, `FrequenciaForm`, `CirioForm`, `RegraCirioForm`**: Formulários atrelados diretamente aos Models descritos acima. Eles dizem quais campos exibir e geram inputs customizados (como campos de data e selects).
- **`CheckinMatriculaForm`**: Formulário solto (não atrelado ao banco diretamente) usado apenas para digitar a matrícula na tela de Check-In rápido.
- **`RegraCirioFormSet`**: Um "FormSet" que permite cadastrar várias `RegrasCirio` de uma só vez na mesma tela em que o `Cirio` é criado.

### `urls.py`
É o arquivo de rotas. Ele conecta as URLs (ex: `/gnsn/mirim/guardas/`) às funções que estão no arquivo `views.py`.

### `views.py`
É o "cérebro" da aplicação. Onde a lógica de negócio acontece. Recebe a requisição do usuário, processa os dados, busca no banco e devolve o HTML renderizado.
- **`group_required()`**: Decorator de segurança. Garante que apenas usuários pertencentes aos grupos 'super' ou 'Mirim_adm' possam acessar as páginas restritas.
- **`home()`**: Renderiza a tela inicial.
- **`enviar_email_participacao()` / `enviar_email_baixa_frequencia()`**: Funções auxiliares. Enviam e-mails reais ou silenciados para o jovem confirmando a presença dele ou alertando caso a frequência caia demais.
- **`dashboard()`**: Lógica pesada que monta o painel gerencial. Ela pega todos os guardas, compara com as regras do Círio ativo e monta relatórios para o gráfico (ex: quantos estão aptos, inaptos ou em situação crítica).
- **Funções CRUD de Categoria (`categoria_list`, `_create`, `_update`)**: Lista, cria e edita as categorias.
- **Funções CRUD de Local (`local_list`, `_create`, `_update`)**: Lista, cria e edita os locais.
- **Funções CRUD de Guarda (`guarda_list`, `_create`, `_update`)**: Lista, cria e edita os guardas mirins.
- **`guarda_detail()`**: View muito importante. Mostra o detalhamento de um guarda específico para o administrador. Faz as contas para exibir barras de progresso informando se o jovem está atingindo a meta de missas e treinamentos daquele Círio.
- **Funções CRUD de Evento (`evento_list`, `_create`, `_update`)**: Lista, cria e edita os eventos.
- **`frequencia_create()`**: Formulário manual completo para dar presença para um guarda em um evento. Se a presença for salva, já engatilha o envio de e-mail e confere se a frequência está baixa para emitir alerta.
- **`checkin_evento()`**: Tela rápida usada em tablets/totens na porta do evento. O usuário digita a matrícula, a função busca o guarda, salva a presença automaticamente, envia o e-mail e recarrega a página para o próximo.
- **`delete_object()`**: Uma função genérica e centralizada que consegue deletar qualquer registro do banco (Guarda, Evento, Local ou Categoria) dependendo do ID e do "tipo" passados via POST.
- **`mirim_consulta()` / `mirim_detail_consulta()`**: Estas rotas são a Área do Guarda. Permitem que um jovem digite seu CPF e matrícula para consultar seu próprio painel de presença e aptidão, sem precisar ter uma conta de administrador no sistema.
- **Funções CRUD de Círio (`cirio_list`, `_form`, `_detail`, `_delete`)**: Gerencia os Círios e suas respectivas metas (regras) através de um FormSet dinâmico na mesma tela.
