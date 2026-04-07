-- Tabela de advogados (já existente)
CREATE TABLE IF NOT EXISTS advogados (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    especialidade VARCHAR(100) NOT NULL,
    disponibilidade VARCHAR(200) NOT NULL
);

-- Inserção de dados de exemplo (apenas se não existirem)
INSERT INTO advogados (nome, especialidade, disponibilidade)
SELECT * FROM (VALUES
    ('Dr. Carlos Mendes',  'Direito Tributário Federal',   'Seg e Qua, 10h às 12h'),
    ('Dra. Ana Paula Lima','Planejamento Tributário',       'Ter e Qui, 14h às 17h'),
    ('Dr. Roberto Farias', 'Execução Fiscal e Defesas',    'Sex, 09h às 12h'),
    ('Dra. Juliana Costa', 'ICMS e Tributos Estaduais',    'Seg e Qui, 15h às 18h')
) AS novos(nome, especialidade, disponibilidade)
WHERE NOT EXISTS (SELECT 1 FROM advogados LIMIT 1);

-- Nova tabela: agendamentos dos clientes
CREATE TABLE IF NOT EXISTS agendamentos (
    id           SERIAL PRIMARY KEY,
    nome_cliente VARCHAR(150) NOT NULL,
    cpf          VARCHAR(20)  NOT NULL,
    telefone     VARCHAR(20)  NOT NULL,
    advogado     VARCHAR(100) NOT NULL,
    horario      VARCHAR(100) NOT NULL,
    criado_em    TIMESTAMP DEFAULT NOW()
);