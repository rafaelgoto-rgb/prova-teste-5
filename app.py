import streamlit as st
import requests
from dotenv import load_dotenv
import os
import uuid

# Carrega variáveis de ambiente
load_dotenv()
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/chat/stream")

# Deriva as URLs necessárias
BASE_URL = API_URL.rsplit("/chat/stream", 1)[0]
CHAT_URL = API_URL
FAQ_LIST_URL = f"{BASE_URL}/faq/"
GENERATE_FAQ_URL = f"{BASE_URL}/faq/generate"
EMAIL_CREATE_URL = f"{BASE_URL}/emails/"
QUIZ_GENERATE_URL = f"{BASE_URL}/quiz/generate"
QUIZ_ANSWER_URL_TEMPLATE = f"{BASE_URL}/quiz/{{quiz_id}}/answer"

# Configuração da página
st.set_page_config(
    page_title="EdTech Futura",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar com navegação
with st.sidebar:
    st.title("EdTech Futura")
    st.markdown("---")
    page = st.radio("Ir para:", ["Chat", "FAQ", "Quiz", "Enviar Email"])
    st.markdown("---")

    if page == "Chat" and st.button("🔄 Limpar Conversa", key="reset_quiz_main"):
        st.session_state.clear()
    if page == "Quiz" and st.button("🔄 Reiniciar Quiz"):
        for key in ["quiz", "current", "score"]:
            if key in st.session_state:
                del st.session_state[key]

# Session state iniciais
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "history" not in st.session_state:
    st.session_state.history = []
if "faqs" not in st.session_state:
    st.session_state.faqs = []
if "email_sent" not in st.session_state:
    st.session_state.email_sent = False

# === Página de Chat ===
if page == "Chat":
    st.header("📄 Chat com Documentação")
    for message in st.session_state.history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    if prompt := st.chat_input("Pergunte sobre Python, FastAPI ou Streamlit..."):
        st.session_state.history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        full_response = ""
        with st.chat_message("assistant"):
            placeholder = st.empty()
            try:
                payload = {"question": prompt, "session_id": st.session_state.session_id}
                response = requests.post(CHAT_URL, json=payload, stream=True, timeout=60)
                response.raise_for_status()
                for chunk in response.iter_content(chunk_size=64):
                    part = chunk.decode("utf-8")
                    full_response += part
                    placeholder.markdown(full_response)
            except requests.RequestException as e:
                placeholder.markdown(f"❌ Erro: {e}")
                full_response = f"Erro: {e}"
        st.session_state.history.append({"role": "assistant", "content": full_response})

# === Página de FAQ ===
elif page == "FAQ":
    st.header("📖 FAQ Consolidada")
    if not st.session_state.faqs:
        try:
            res = requests.get(FAQ_LIST_URL, timeout=10)
            res.raise_for_status()
            st.session_state.faqs = res.json()
        except Exception as e:
            st.error(f"Não foi possível carregar FAQs: {e}")
    if st.button("🔄 Gerar FAQ a partir dos e-mails"):
        try:
            res = requests.post(GENERATE_FAQ_URL, timeout=180)
            res.raise_for_status()
            st.session_state.faqs = res.json()
            st.success("✅ FAQ gerada com sucesso!")
        except Exception as e:
            st.error(f"Erro ao gerar FAQ: {e}")
    st.markdown("---")
    for faq in st.session_state.faqs:
        with st.expander(faq["question"]):
            st.markdown(faq["answer"])
            st.markdown(f"**Fonte:** {faq['excerpt']}  \n{faq['link']}")

# === Página de Emails ===
elif page == "Enviar Email":
    st.header("✉️ Enviar E-mails")

    # Se o e-mail foi enviado, mostra sucesso e reseta estado
    if st.session_state.get("email_sent", False):
        st.success("✅ E-mail simulado enviado com sucesso!")
        st.session_state.email_sent = False

    with st.form("email_form"):
        sender = st.text_input("Remetente (sender):", "")
        subject = st.text_input("Assunto (subject):", "")
        body = st.text_area("Corpo da mensagem (body):", height=150)
        submitted = st.form_submit_button("📤 Enviar e-mail")

    if submitted:
        if not sender or not subject or not body:
            st.warning("Por favor, preencha todos os campos antes de enviar.")
        else:
            try:
                payload = {"sender": sender, "subject": subject, "body": body}
                res = requests.post(EMAIL_CREATE_URL, json=payload, timeout=10)
                res.raise_for_status()
                st.session_state.email_sent = True
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao enviar e-mail: {e}")
