# ⚖️ Assistente Jurídico Tributário com IA e Automação

Este projeto implementa um **Agente de IA especializado em triagem jurídica tributária**, capaz de analisar problemas, identificar soluções legais, indicar especialistas e realizar agendamentos automatizados.

Desenvolvido como parte de um desafio técnico para a vaga de **Analista de IA Júnior**.

---

## 🎯 Objetivo

Construir um assistente inteligente que:

* Analise problemas jurídicos tributários
* Utilize base de conhecimento estruturada (RAG)
* Indique o advogado mais adequado
* Colete dados do cliente de forma estruturada
* Realize agendamento automático
* Dispare automações (email e webhook)

---

## 🧠 Stack Tecnológica

* **LLM:** Google Gemini 2.5 Flash
* **Framework:** LangChain (Agents + Tools)
* **Backend:** Python 3.10+
* **Interface:** Streamlit
* **Banco de Dados:** PostgreSQL
* **Automação:** SMTP (Email) + Webhook Simulado
* **Containerização:** Docker + Docker Compose

---

## ⚠️ Observação sobre o Modelo

O desafio solicitava GPT-4o ou Gemini 1.5.

Devido a limitações de acesso, foi utilizado:

👉 **Gemini 2.5 Flash**

A arquitetura permanece totalmente aderente ao desafio.

---

## 🏗️ Arquitetura do Sistema

O sistema foi projetado com base em **agentes com ferramentas (Tools)**, seguindo uma arquitetura modular:

### 🔹 1. Base de Conhecimento

* **RAG Local:** Documentos `.txt` e `.md` na pasta `/data`
* **Banco de Dados:** Lista de advogados e agendamentos

---

### 🔹 2. Tools do Agente

#### 📚 `consultar_base_tributaria`

* Analisa o problema jurídico usando RAG
* Identifica:

  * Se há solução jurídica
  * Qual o caminho recomendado
  * Qual especialidade é necessária

---

#### 📅 `salvar_dados_e_agendar`

* Salva os dados do cliente no PostgreSQL
* Registra o agendamento
* Dispara envio de email automático
* Retorna confirmação estruturada

---

#### 🚨 `disparar_automacao_escalonamento`

* Simula envio de webhook:

```bash
>> [WEBHOOK → n8n] ESCALONAMENTO: motivo
```

* Acionado em casos críticos ou solicitação de humano

---

## 🔥 Engenharia de Prompt (Diferencial Principal)

O agente é controlado por um **System Prompt estruturado com fluxo obrigatório**, evitando respostas livres e garantindo previsibilidade.

---

### 🧭 Fluxo de Atendimento

O agente segue rigorosamente as etapas:

1. **Coleta do problema**
2. **Validação da descrição**

   * Vaga → solicita mais detalhes (template guiado)
   * Fora do escopo → redireciona
3. **Consulta na base jurídica (RAG)**
4. **Indicação de advogado**
5. **Coleta de dados (Nome, CPF, Telefone)**
6. **Agendamento automático**

---

### 🛑 Regras Críticas

* Nunca inventar informações
* Não fornecer parecer jurídico definitivo
* Utilizar apenas dados disponíveis
* Validar dados antes de salvar
* Escalonar em casos críticos

---

### ⚡ Gatilhos de Automação

A automação é acionada quando:

* Usuário pede atendimento humano
* Linguagem agressiva
* Problemas graves relatados

---

## 🗄️ Banco de Dados

### 👨‍⚖️ Tabela: `advogados`

* Nome
* Especialidade
* Disponibilidade

### 📅 Tabela: `agendamentos`

* Nome do cliente
* CPF
* Telefone
* Advogado
* Horário
* Timestamp automático

---

### 🔄 Fluxo Integrado

1. IA analisa o problema
2. Identifica especialidade
3. Consulta advogados disponíveis
4. Sugere profissional
5. Coleta dados
6. Persiste no banco
7. Envia email

---

## 📧 Automação de Email

Após o agendamento:

* Envio automático via SMTP (Gmail)
* Template HTML estruturado
* Notificação para equipe

---

## 🐳 Execução com Docker

### 1. Configurar `.env`

```bash
GOOGLE_API_KEY=sua_chave

DATABASE_URL=postgresql://admin_user:senha_segura_123@db:5432/escritorio_db

EMAIL_REMETENTE=seuemail@gmail.com
EMAIL_SENHA_APP=sua_senha_de_app
EMAIL_DESTINATARIO=seuemail@gmail.com
```

---

### 2. Subir o ambiente

```bash
docker-compose up --build
```

---

### 3. Acessar

👉 http://localhost:8501

---

## 💡 Diferenciais do Projeto

* ✔ Fluxo conversacional estruturado (não apenas chatbot)
* ✔ Engenharia de prompt avançada
* ✔ Integração real com banco de dados
* ✔ Automação completa (email + webhook)
* ✔ RAG aplicado ao domínio jurídico
* ✔ Coleta e validação de dados do usuário
* ✔ Arquitetura pronta para produção

---

## ⚖️ Considerações sobre LGPD

Os dados (ex: CPF) são utilizados apenas para simulação.

Em ambiente real, seriam aplicadas:

* Criptografia de dados sensíveis
* Controle de acesso
* Políticas de retenção
* Conformidade com LGPD

---

## 📌 Conclusão

O projeto demonstra a capacidade de construir um agente de IA que:

* Segue fluxos estruturados
* Evita alucinação
* Integra com sistemas reais
* Resolve problemas de negócio

---

## 👨‍💻 Autor

William Jesus
