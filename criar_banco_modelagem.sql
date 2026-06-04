PRAGMA foreign_keys = ON;

-- 1. TABELA CENTRAL: PESSOA
CREATE TABLE IF NOT EXISTS PESSOA (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nome            VARCHAR(200)    NOT NULL,
    email           VARCHAR(150)    UNIQUE,
    telefone        VARCHAR(50),
    cpf             VARCHAR(14)     UNIQUE,
    rg              VARCHAR(45)     UNIQUE,
    estado_civil    VARCHAR(50),
    genero          VARCHAR(50),
    data_nascimento DATE,
    criado_em       DATE            DEFAULT (DATE('now')),
    atualizado_em   DATE            DEFAULT (DATE('now'))
);

-- ============================================================
-- 2. TABELA: ENDERECO (one_to_one com PESSOA)
-- ============================================================
CREATE TABLE IF NOT EXISTS ENDERECO (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    pessoa_id       BIGINT          NOT NULL UNIQUE,
    logradouro      VARCHAR(200),
    complemento     VARCHAR(200),
    cidade          VARCHAR(100),
    bairro          VARCHAR(100),
    cep             VARCHAR(20),
    uf              VARCHAR(10),
    numero          VARCHAR(20),
    criado_em       DATE            DEFAULT (DATE('now')),
    atualizado_em   DATE            DEFAULT (DATE('now')),
    FOREIGN KEY (pessoa_id) REFERENCES PESSOA(id) ON DELETE CASCADE
);

-- ============================================================
-- 3. TABELA: FICHA_SAUDE (one_to_one com PESSOA)
-- ============================================================
CREATE TABLE IF NOT EXISTS FICHA_SAUDE (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    pessoa_id                   BIGINT      NOT NULL UNIQUE,

    autismo                     TINYINT     DEFAULT 0,
    tdah                        TINYINT     DEFAULT 0,
    alzheimer                   TINYINT     DEFAULT 0,
    demencia                    TINYINT     DEFAULT 0,
    parkinson                   TINYINT     DEFAULT 0,
    diabetes                    TINYINT     DEFAULT 0,
    hipertensao                 TINYINT     DEFAULT 0,
    problema_cardiaco           TINYINT     DEFAULT 0,
    problema_renal              TINYINT     DEFAULT 0,
    osteoporose                 TINYINT     DEFAULT 0,
    artrite                     TINYINT     DEFAULT 0,

    usa_cadeira_rodas           TINYINT     DEFAULT 0,
    usa_andador                 TINYINT     DEFAULT 0,
    usa_bengala                 TINYINT     DEFAULT 0,
    deficiencia_visual          TINYINT     DEFAULT 0,
    deficiencia_auditiva        TINYINT     DEFAULT 0,
    usa_protese                 TINYINT     DEFAULT 0,

    depressao                   TINYINT     DEFAULT 0,
    ansiedade                   TINYINT     DEFAULT 0,

    alergia                     VARCHAR(250),
    intolerancia_alimentar      VARCHAR(250),
    doenca_cronica              VARCHAR(250),
    uso_medicamento_controlado  VARCHAR(250),
    plano_saude                 VARCHAR(250),
    tipo_sanguineo              VARCHAR(150),

    contato_emergencia_nome     VARCHAR(200),
    contato_emergencia_telefone VARCHAR(50),

    observacao                  VARCHAR(250),

    criado_em                   DATE        DEFAULT (DATE('now')),
    atualizado_em               DATE        DEFAULT (DATE('now')),

    FOREIGN KEY (pessoa_id) REFERENCES PESSOA(id) ON DELETE CASCADE
);

-- 4. TABELA: GUARDA (one_to_one com PESSOA)
CREATE TABLE IF NOT EXISTS GUARDA (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    pessoa_id               BIGINT      NOT NULL UNIQUE,
    turma                   INT,
    tipo                    VARCHAR(20) CHECK(tipo IN ('Mirim')),
    paroquia                VARCHAR(200),
    matricula               VARCHAR(20) UNIQUE,
    tamanho_camisa          VARCHAR(10),
    status                  VARCHAR(20) DEFAULT 'ativo',
    observacao              VARCHAR(200),
    data_ingresso           DATE,
    is_ativo                TINYINT     DEFAULT 1,
    criado_em               DATE        DEFAULT (DATE('now')),
    atualizado_em           DATE        DEFAULT (DATE('now')),
    FOREIGN KEY (pessoa_id) REFERENCES PESSOA(id) ON DELETE CASCADE
);

-- 5. TABELA ASSOCIATIVA: RESPONSAVEL_GUARDA (many_to_many)
CREATE TABLE IF NOT EXISTS RESPONSAVEL_GUARDA (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    guarda_id       BIGINT  NOT NULL,
    pessoa_id       BIGINT  NOT NULL,
    parentesco      VARCHAR(50),
    FOREIGN KEY (guarda_id) REFERENCES GUARDA(id) ON DELETE CASCADE,
    FOREIGN KEY (pessoa_id) REFERENCES PESSOA(id) ON DELETE CASCADE,
    UNIQUE(guarda_id, pessoa_id)
);

-- 6. TABELA ASSOCIATIVA: PADRINHO_GUARDA (many_to_many)
CREATE TABLE IF NOT EXISTS PADRINHO_GUARDA (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    guarda_id       BIGINT  NOT NULL,
    padrinho_id     BIGINT  NOT NULL,
    FOREIGN KEY (guarda_id) REFERENCES GUARDA(id) ON DELETE CASCADE,
    FOREIGN KEY (padrinho_id) REFERENCES GUARDA(id) ON DELETE CASCADE,
    UNIQUE(guarda_id, padrinho_id)
);

-- 7. TABELA: SACRAMENTO (one_to_many com GUARDA)
CREATE TABLE IF NOT EXISTS SACRAMENTO (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    guarda_id               BIGINT      NOT NULL,
    batismo                 TINYINT     DEFAULT 0,
    primeira_eucaristia     TINYINT     DEFAULT 0,
    crisma                  TINYINT     DEFAULT 0,
    ordem                   TINYINT     DEFAULT 0,
    data_batismo            DATE,
    data_primeira_eucaristia DATE,
    data_crisma             DATE,
    FOREIGN KEY (guarda_id) REFERENCES GUARDA(id) ON DELETE CASCADE
);

-- 8. TABELA: CIRIO
CREATE TABLE IF NOT EXISTS CIRIO (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    ano             INT             NOT NULL UNIQUE,
    ativo           TINYINT         DEFAULT 1,
    inicio          DATE,
    termino         DATE,
    criado_em       DATE            DEFAULT (DATE('now')),
    atualizado_em   DATE            DEFAULT (DATE('now'))
);

-- 9a. TABELA: CATEGORIA_EVENTO
CREATE TABLE IF NOT EXISTS CATEGORIA_EVENTO (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nome            VARCHAR(100)    NOT NULL UNIQUE,
    is_ativo        TINYINT         DEFAULT 1,
    criado_em       DATE            DEFAULT (DATE('now')),
    atualizado_em   DATE            DEFAULT (DATE('now'))
);

-- 9b. TABELA: REGRA_CIRIO (pivot entre CIRIO e CATEGORIA_EVENTO)
CREATE TABLE IF NOT EXISTS REGRA_CIRIO (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    cirio_id                BIGINT  NOT NULL,
    categoria_id            BIGINT  NOT NULL,
    quantidade_necessaria   INT     NOT NULL DEFAULT 0,
    FOREIGN KEY (cirio_id)      REFERENCES CIRIO(id) ON DELETE CASCADE,
    FOREIGN KEY (categoria_id)  REFERENCES CATEGORIA_EVENTO(id) ON DELETE CASCADE,
    UNIQUE(cirio_id, categoria_id)
);

-- 10. TABELA: LOCAL
CREATE TABLE IF NOT EXISTS LOCAL (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nome            VARCHAR(200)    NOT NULL UNIQUE,
    is_ativo        TINYINT         DEFAULT 1,
    criado_em       DATE            DEFAULT (DATE('now')),
    atualizado_em   DATE            DEFAULT (DATE('now'))
);

-- 11. TABELA: EVENTO
CREATE TABLE IF NOT EXISTS EVENTO (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    categoria_id    BIGINT          NOT NULL,
    local_id        BIGINT          NOT NULL,
    data            DATE,
    hora            DATETIME,
    criado_em       DATE            DEFAULT (DATE('now')),
    atualizado_em   DATE            DEFAULT (DATE('now')),
    FOREIGN KEY (categoria_id) REFERENCES CATEGORIA_EVENTO(id) ON DELETE RESTRICT,
    FOREIGN KEY (local_id)     REFERENCES LOCAL(id) ON DELETE RESTRICT
);

-- 12. TABELA: FREQUENCIA (many_to_many entre GUARDA e EVENTO)
CREATE TABLE IF NOT EXISTS FREQUENCIA (
    id                              INTEGER PRIMARY KEY AUTOINCREMENT,
    guarda_id                       BIGINT      NOT NULL,
    evento_id                       BIGINT      NOT NULL,
    data_registro                   DATE,
    hora_registro                   DATETIME,
    local_provisorio                VARCHAR(200),
    reconhecimento_facial           TINYINT     DEFAULT 0,
    observacao                      VARCHAR(250),
    criado_em                       DATE        DEFAULT (DATE('now')),
    atualizado_em                   DATE        DEFAULT (DATE('now')),
    FOREIGN KEY (guarda_id) REFERENCES GUARDA(id) ON DELETE CASCADE,
    FOREIGN KEY (evento_id) REFERENCES EVENTO(id) ON DELETE CASCADE
);

-- 13. TABELA: SETOR
CREATE TABLE IF NOT EXISTS SETOR (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nome            VARCHAR(200)    NOT NULL,
    localizacao     VARCHAR(200),
    is_ativo        TINYINT         DEFAULT 1,
    criado_em       DATE            DEFAULT (DATE('now')),
    atualizado_em   DATE            DEFAULT (DATE('now'))
);

-- 14. TABELA: CATEGORIA_MATERIAL
CREATE TABLE IF NOT EXISTS CATEGORIA_MATERIAL (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nome            VARCHAR(200)    NOT NULL,
    descricao       VARCHAR(200),
    is_ativo        TINYINT         DEFAULT 1,
    criado_em       DATE            DEFAULT (DATE('now')),
    atualizado_em   DATE            DEFAULT (DATE('now'))
);

-- 15. TABELA: MATERIAL
CREATE TABLE IF NOT EXISTS MATERIAL (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    categoria_id        BIGINT          NOT NULL,
    setor_id            BIGINT,
    nome                VARCHAR(200)    NOT NULL,
    numero_patrimonio   VARCHAR(50)     UNIQUE,
    status              VARCHAR(20)     DEFAULT 'disponivel'
                        CHECK(status IN ('disponivel', 'indisponivel', 'manutencao', 'defeito', 'problema')),
    qtd_disponivel      BIGINT          DEFAULT 0,
    data_cadastro       DATE            DEFAULT (DATE('now')),
    criado_em           DATE            DEFAULT (DATE('now')),
    atualizado_em       DATE            DEFAULT (DATE('now')),
    FOREIGN KEY (categoria_id) REFERENCES CATEGORIA_MATERIAL(id) ON DELETE RESTRICT,
    FOREIGN KEY (setor_id)     REFERENCES SETOR(id) ON DELETE SET NULL
);

-- 16. TABELA: EQUIPE
CREATE TABLE IF NOT EXISTS EQUIPE (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nome            VARCHAR(100)    NOT NULL UNIQUE,
    criado_em       DATE            DEFAULT (DATE('now')),
    atualizado_em   DATE            DEFAULT (DATE('now'))
);

-- 17. TABELA: ESTOQUE
CREATE TABLE IF NOT EXISTS ESTOQUE (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    material_id     BIGINT          NOT NULL,
    quantidade      BIGINT          DEFAULT 0,
    validade        DATE,
    data_solicitacao DATE,
    criado_em       DATE            DEFAULT (DATE('now')),
    atualizado_em   DATE            DEFAULT (DATE('now')),
    FOREIGN KEY (material_id) REFERENCES MATERIAL(id) ON DELETE CASCADE
);

-- 18. TABELA: EMPRESTIMO
CREATE TABLE IF NOT EXISTS EMPRESTIMO (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    material_id                 BIGINT      NOT NULL,
    solicitante_id              BIGINT      NOT NULL,
    retirante_id                BIGINT,
    responsavel_patrimonio_id   BIGINT,
    quantidade                  BIGINT      DEFAULT 0,
    data_solicitacao            DATE,
    data_retirada               DATE,
    status                      VARCHAR(20) DEFAULT 'solicitado'
                                CHECK(status IN ('solicitado', 'aprovado', 'retirado', 'devolvido', 'atrasado', 'cancelado')),
    criado_em                   DATE        DEFAULT (DATE('now')),
    atualizado_em               DATE        DEFAULT (DATE('now')),
    FOREIGN KEY (material_id)                REFERENCES MATERIAL(id) ON DELETE RESTRICT,
    FOREIGN KEY (solicitante_id)             REFERENCES GUARDA(id) ON DELETE RESTRICT,
    FOREIGN KEY (retirante_id)               REFERENCES GUARDA(id) ON DELETE RESTRICT,
    FOREIGN KEY (responsavel_patrimonio_id)   REFERENCES GUARDA(id) ON DELETE RESTRICT
);

-- 19. TABELA: CAMISA
CREATE TABLE IF NOT EXISTS CAMISA (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    equipe_id       BIGINT          NOT NULL,
    guarda_id       BIGINT          NOT NULL,
    pessoa_id       BIGINT          NOT NULL,
    entregador_id   BIGINT,
    criador_id      BIGINT,
    ano             INT,
    tamanho_camisa  VARCHAR(10),
    situacao        TINYINT         DEFAULT 0,
    recebido        TINYINT         DEFAULT 0,
    recebedor       VARCHAR(200),
    criado_em       DATE            DEFAULT (DATE('now')),
    atualizado_em   DATE            DEFAULT (DATE('now')),
    FOREIGN KEY (equipe_id)     REFERENCES EQUIPE(id) ON DELETE RESTRICT,
    FOREIGN KEY (guarda_id)     REFERENCES GUARDA(id) ON DELETE RESTRICT,
    FOREIGN KEY (pessoa_id)     REFERENCES PESSOA(id) ON DELETE RESTRICT,
    FOREIGN KEY (entregador_id) REFERENCES GUARDA(id) ON DELETE RESTRICT,
    FOREIGN KEY (criador_id)    REFERENCES GUARDA(id) ON DELETE RESTRICT
);

-- 20. TABELA: CAMISA_LOG
CREATE TABLE IF NOT EXISTS CAMISA_LOG (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    camisa_id           BIGINT      NOT NULL,
    usuario_id          BIGINT,
    tamanho_antigo      VARCHAR(10),
    tamanho_novo        VARCHAR(10),
    situacao_antiga     TINYINT,
    situacao_nova       TINYINT,
    justificativa       VARCHAR(200),
    data_alteracao      DATE        DEFAULT (DATE('now')),
    FOREIGN KEY (camisa_id)  REFERENCES CAMISA(id) ON DELETE CASCADE,
    FOREIGN KEY (usuario_id) REFERENCES GUARDA(id) ON DELETE SET NULL
);

-- 21. TABELA: USUARIO (one_to_one com PESSOA)
CREATE TABLE IF NOT EXISTS USUARIO (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    pessoa_id           BIGINT      NOT NULL UNIQUE,
    usuario             VARCHAR(50) NOT NULL UNIQUE,
    senha               VARCHAR(255) NOT NULL,
    is_super_usuario    TINYINT     DEFAULT 0,
    is_ativo            TINYINT     DEFAULT 1,
    trocar_senha        TINYINT     DEFAULT 1,
    criado_em           DATE        DEFAULT (DATE('now')),
    atualizado_em       DATE        DEFAULT (DATE('now')),
    FOREIGN KEY (pessoa_id) REFERENCES PESSOA(id) ON DELETE CASCADE
);

