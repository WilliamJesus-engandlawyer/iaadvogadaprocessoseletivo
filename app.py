import os
import glob
import smtplib
import streamlit as st
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import tool
from langchain_core.messages import HumanMessage, AIMessage

# ─────────────────────────────────────────────
# 1. CONFIGURAÇÕES (tudo vem do .env)
# ─────────────────────────────────────────────
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))


# ─────────────────────────────────────────────
# 2. BASE DE CONHECIMENTO DINÂMICA (POSTGRES)
# ─────────────────────────────────────────────
def get_advogados_context() -> str:
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT nome, especialidade, disponibilidade FROM advogados")
            )
            advogados = result.fetchall()
            ctx = "\nLISTA DE ADVOGADOS E AGENDAS:\n"
            for adv in advogados:
                ctx += (
                    f"- {adv.nome}: Especialista em {adv.especialidade}. "
                    f"Disponível: {adv.disponibilidade}\n"
                )
            return ctx
    except Exception as e:
        print(f"[DB ERROR] {e}")
        return "Erro ao carregar base de especialistas do banco de dados."


# ─────────────────────────────────────────────
# 3. RAG LOCAL – pasta /data
# ─────────────────────────────────────────────
def load_rag_knowledge(data_dir: str = "data") -> str:
    docs: list[str] = []
    for pattern in ["**/*.txt", "**/*.md"]:
        for filepath in glob.glob(os.path.join(data_dir, pattern), recursive=True):
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read().strip()
                    if content:
                        filename = os.path.relpath(filepath, data_dir)
                        docs.append(f"[Documento: {filename}]\n{content}")
            except Exception as e:
                print(f"[RAG ERROR] {filepath}: {e}")

    if not docs:
        return "(Nenhum documento encontrado na pasta 'data'.)"
    return "\n\n---\n\n".join(docs)[:30_000]


# ─────────────────────────────────────────────
# 4. ENVIO DE EMAIL (isolado — fácil de trocar)
# ─────────────────────────────────────────────
def enviar_email(nome: str, cpf: str, telefone: str, advogado: str, horario: str) -> bool:
    """
    Envia email via Gmail SMTP com Senha de App.
    Para configurar: https://support.google.com/accounts/answer/185833
    Adicione no .env:
      EMAIL_REMETENTE=seuemail@gmail.com
      EMAIL_SENHA_APP=xxxx xxxx xxxx xxxx   (senha de app de 16 dígitos)
      EMAIL_DESTINATARIO=willianjesus554@gmail.com
    """
    smtp_user    = os.getenv("EMAIL_REMETENTE")
    smtp_pass    = os.getenv("EMAIL_SENHA_APP")
    destinatario = os.getenv("EMAIL_DESTINATARIO", "willianjesus554@gmail.com")

    if not smtp_user or not smtp_pass:
        print("[EMAIL] Variáveis EMAIL_REMETENTE ou EMAIL_SENHA_APP não configuradas.")
        return False

    assunto = f"📋 Novo Agendamento – {nome}"
    corpo = f"""
    <h2 style="color:#1a3c5e;">Novo Agendamento Recebido</h2>
    <table border="1" cellpadding="10" cellspacing="0" style="border-collapse:collapse;font-family:Arial;">
      <tr style="background:#f0f4f8;"><td><b>Nome</b></td><td>{nome}</td></tr>
      <tr><td><b>CPF</b></td><td>{cpf}</td></tr>
      <tr style="background:#f0f4f8;"><td><b>Telefone</b></td><td>{telefone}</td></tr>
      <tr><td><b>Advogado</b></td><td>{advogado}</td></tr>
      <tr style="background:#f0f4f8;"><td><b>Horário</b></td><td>{horario}</td></tr>
    </table>
    <p style="color:#555;">Os dados foram salvos no banco de dados do sistema.</p>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = assunto
    msg["From"]    = smtp_user
    msg["To"]      = destinatario
    msg.attach(MIMEText(corpo, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, destinatario, msg.as_string())
        print(f"[EMAIL] Enviado com sucesso para {destinatario}")
        return True
    except Exception as e:
        print(f"[EMAIL ERROR] {e}")
        return False


# ─────────────────────────────────────────────
# 5. TOOLS DO AGENTE
# ─────────────────────────────────────────────
@tool
def consultar_base_tributaria(problema_descrito: str) -> str:
    """
    Consulta a base de conhecimento tributária (RAG local) para:
    1. Verificar se o problema tem solução jurídica conhecida.
    2. Identificar qual área do direito tributário se aplica.
    3. Sugerir qual tipo de especialista é mais adequado.
    Use SEMPRE antes de indicar um advogado.
    """
    rag = load_rag_knowledge()
    llm_rag = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0,
        google_api_key=os.getenv("GOOGLE_API_KEY"),
    )
    query = f"""
Com base APENAS nos documentos tributários abaixo, responda em português:
1. O problema descrito tem solução jurídica? (sim/não/parcialmente)
2. Qual é a solução ou caminho legal recomendado?
3. Qual especialidade tributária é mais indicada para este caso?

PROBLEMA DO CLIENTE:
{problema_descrito}

DOCUMENTOS TRIBUTÁRIOS:
{rag}

Seja objetivo. Se o problema não estiver coberto pelos documentos, diga claramente.
"""
    try:
        return llm_rag.invoke(query).content
    except Exception as e:
        return f"Não foi possível consultar a base de conhecimento: {e}"


@tool
def salvar_dados_e_agendar(
    nome: str,
    cpf: str,
    telefone: str,
    advogado: str,
    horario: str,
) -> str:
    """
    Salva os dados do cliente no banco de dados E envia email de notificação.
    Use SOMENTE após o cliente confirmar o agendamento E fornecer nome, CPF e telefone.
    Parâmetros:
      - nome: nome completo do cliente.
      - cpf: CPF do cliente (somente números ou formatado).
      - telefone: telefone/celular do cliente com DDD.
      - advogado: nome do advogado escolhido.
      - horario: horário/período confirmado.
    """
    # Salva no banco
    try:
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO agendamentos (nome_cliente, cpf, telefone, advogado, horario)
                VALUES (:nome, :cpf, :telefone, :advogado, :horario)
            """), {
                "nome": nome,
                "cpf": cpf,
                "telefone": telefone,
                "advogado": advogado,
                "horario": horario,
            })
        db_status = "✅ Dados salvos no sistema com sucesso."
    except Exception as e:
        print(f"[DB SAVE ERROR] {e}")
        db_status = "⚠️ Problema ao salvar no banco. Nossa equipe foi avisada."

    # Envia email
    email_ok = enviar_email(nome, cpf, telefone, advogado, horario)
    email_status = (
        "✅ Notificação enviada para a equipe."
        if email_ok
        else "⚠️ Email de notificação não pôde ser enviado agora, mas o agendamento foi registrado."
    )

    return (
        f"Agendamento concluído!\n\n"
        f"{db_status}\n"
        f"{email_status}\n\n"
        f"📋 Resumo:\n"
        f"• Cliente: {nome}\n"
        f"• Advogado: {advogado}\n"
        f"• Horário: {horario}\n\n"
        "Você receberá uma confirmação em breve. Obrigado! 😊"
    )


@tool
def disparar_automacao_escalonamento(motivo: str) -> str:
    """
    Aciona escalonamento para atendente humano quando:
    - O cliente solicita falar com humano.
    - O cliente está agressivo ou usa linguagem ofensiva.
    - Há erro grave ou emergência relatada.
    """
    print(f"\n>> [WEBHOOK → n8n] ESCALONAMENTO: {motivo}")
    return (
        "Protocolo de atenção especial ativado. "
        "Um consultor humano foi notificado e entrará em contato em breve."
    )


tools = [
    consultar_base_tributaria,
    salvar_dados_e_agendar,
    disparar_automacao_escalonamento,
]


# ─────────────────────────────────────────────
# 6. PROMPT ENGINEERING
# ─────────────────────────────────────────────
base_estatica = """
HORÁRIO GERAL DO ESCRITÓRIO: Segunda a Sexta, 09h às 18h.
PRAZO DE RETORNO: Até 5 dias úteis.
POLÍTICA: Cancelamentos devem ser feitos com 24h de antecedência.
"""

contexto_advogados = get_advogados_context()

system_prompt = f"""
Você é o assistente virtual de triagem jurídica de um escritório de advocacia tributária.
Sua persona: educado, empático, conciso e extremamente prestativo.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FLUXO OBRIGATÓRIO DE ATENDIMENTO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PASSO 1 – COLETA DO PROBLEMA
  Se o cliente ainda não descreveu o problema, peça que descreva
  detalhadamente a situação tributária ou jurídica que está enfrentando.

PASSO 2 – VALIDAÇÃO DA DESCRIÇÃO
  a) VAGA ou CONFUSA → acione o GATILHO DE ORIENTAÇÃO (veja abaixo).
  b) FORA DO ESCOPO → explique o foco do escritório e pergunte se há
     questão tributária/jurídica que possa ajudar.
  c) CLARA e RELEVANTE → avance para o Passo 3.

PASSO 3 – CONSULTA NA BASE DE CONHECIMENTO
  Use 'consultar_base_tributaria' com o problema descrito.
  Informe ao cliente: se tem solução jurídica, qual é e qual especialidade é necessária.

PASSO 4 – INDICAÇÃO DO ADVOGADO
  Com base na especialidade identificada e na lista de advogados,
  indique o profissional mais adequado e os horários disponíveis.
  Nunca invente nomes ou horários que não estejam na lista.

PASSO 5 – COLETA DE DADOS PESSOAIS
  Após o cliente confirmar que quer agendar, solicite os três dados abaixo
  (pode pedir todos de uma vez):
  • Nome completo
  • CPF
  • Telefone com DDD
  Após receber os três, chame 'salvar_dados_e_agendar' imediatamente.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GATILHO DE ORIENTAÇÃO (descrição confusa ou vaga)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Quando a descrição for difícil de entender, responda exatamente:

"Poxa, não consegui compreender bem o seu problema. Para te ajudar da melhor forma, poderia descrever assim?

📋 Modelo sugerido:
1. O que aconteceu? (Ex: recebi uma notificação fiscal, fui autuado, tenho dívida com a Receita…)
2. Quem está envolvido? (Ex: pessoa física, empresa, órgão público…)
3. Qual é o principal problema ou dúvida? (Ex: não sei se devo pagar, quero contestar, preciso parcelar…)

Quanto mais detalhes, melhor poderei te direcionar ao especialista certo! 😊"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REGRAS GERAIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Responda APENAS com base nas informações fornecidas.
- Se o cliente estiver AGRESSIVO ou PEDIR FALAR COM HUMANO, use 'disparar_automacao_escalonamento'.
- Use linguagem simples, sem jargões jurídicos desnecessários.
- Nunca dê pareceres jurídicos definitivos — você é um triador, não um advogado.
- Nunca salve dados incompletos. Certifique-se de ter nome, CPF e telefone antes de chamar 'salvar_dados_e_agendar'.

{base_estatica}
{contexto_advogados}
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])


# ─────────────────────────────────────────────
# 7. INTERFACE STREAMLIT
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Escritório Tributário AI",
    page_icon="⚖️",
    layout="centered",
)

st.title("⚖️ Assistente Jurídico Tributário")
st.caption(
    "Olá! Sou o assistente virtual do escritório. "
    "Conte-me seu problema e vou te direcionar ao especialista certo."
)

if "messages" not in st.session_state:
    st.session_state.messages = []

if "agent_executor" not in st.session_state:
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0,
        google_api_key=os.getenv("GOOGLE_API_KEY"),
    )
    agent = create_tool_calling_agent(llm, tools, prompt)
    st.session_state.agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=8,
        early_stopping_method="generate",
    )

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if user_input := st.chat_input("Descreva sua situação tributária ou jurídica..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Analisando sua situação..."):
            history = []
            for m in st.session_state.messages[:-1]:
                if m["role"] == "user":
                    history.append(HumanMessage(content=m["content"]))
                else:
                    history.append(AIMessage(content=m["content"]))
            try:
                response = st.session_state.agent_executor.invoke({
                    "input": user_input,
                    "chat_history": history,
                })
                full_response = response["output"]
            except Exception as e:
                full_response = (
                    "Desculpe, tive um problema técnico. "
                    "Por favor, tente novamente ou aguarde contato da nossa equipe."
                )
                print(f"[AGENT ERROR] {e}")

        st.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})