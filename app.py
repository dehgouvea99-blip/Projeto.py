import streamlit as st
from openai import OpenAI
import pypdf

# ==========================================
# CONFIGURAÇÃO DA PÁGINA E ESTILO VISUAL
# ==========================================
st.set_page_config(
    page_title="ChatBot Acadêmico com RAG",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Estilização CSS customizada complementar
st.markdown("""
    <style>
    .stApp {
        background-color: #f8f9fa;
    }
    [data-testid="stSidebar"] {
        background-color: #f1f5f9;
        border-right: 1px solid #e2e8f0;
    }
    h1 {
        color: #1e293b;
        font-weight: 700;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# GERENCIAMENTO DE ESTADO (SESSION STATE)
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "file_context" not in st.session_state:
    st.session_state.file_context = ""

if "uploaded_file_name" not in st.session_state:
    st.session_state.uploaded_file_name = None

# ==========================================
# BARRA LATERAL (CONFIGURAÇÕES E RAG)
# ==========================================
with st.sidebar:
    st.header("⚙️ Credenciais da API")
    st.markdown("Insira seus dados do **Microsoft Foundry** para conectar o assistente:")
    
    # Campos dinâmicos para inserção segura das credenciais pelo usuário
    minha_chave = st.text_input("Chave da API (API Key)", type="password", placeholder="Insira sua chave aqui...")
    meu_endpoint = st.text_input("Endpoint do Serviço", value="https://marcelomaffeis-05082026-resource.services.ai.azure.com/openai/v1/")
    meu_modelo = st.text_input("Nome do Deployment (Modelo)", value="gpt-4.1-mini")
    
    st.markdown("---")
    
    st.header("📂 Base de Conhecimento (RAG)")
    st.markdown("Envie um documento de referência (**PDF** ou **TXT**) para contextualizar as respostas.")
    
    uploaded_file = st.file_uploader("Escolha um arquivo", type=["pdf", "txt"])
    
    if uploaded_file is not None:
        # Processa o arquivo apenas se for um arquivo novo (otimização de performance)
        if st.session_state.uploaded_file_name != uploaded_file.name:
            st.session_state.uploaded_file_name = uploaded_file.name
            st.session_state.file_context = ""
            
            file_extension = uploaded_file.name.split(".")[-1].lower()
            
            if file_extension == "pdf":
                try:
                    reader = pypdf.PdfReader(uploaded_file)
                    extracted_text = []
                    for page in reader.pages:
                        text = page.extract_text()
                        if text:
                            extracted_text.append(text)
                    st.session_state.file_context = "\n".join(extracted_text)
                    st.success(f"PDF '{uploaded_file.name}' processado com sucesso!")
                except Exception as e:
                    st.error(f"Erro ao ler o arquivo PDF: {e}")
                    
            elif file_extension == "txt":
                try:
                    st.session_state.file_context = uploaded_file.read().decode("utf-8")
                    st.success(f"TXT '{uploaded_file.name}' processado com sucesso!")
                except Exception as e:
                    st.error(f"Erro ao ler o arquivo TXT: {e}")
    else:
        if st.session_state.uploaded_file_name is not None:
            st.session_state.uploaded_file_name = None
            st.session_state.file_context = ""
            st.info("Base de conhecimento limpa.")

    if st.session_state.file_context:
        st.info(f"Contexto ativo: ~{len(st.session_state.file_context)} caracteres.")
            
    st.markdown("---")
    st.markdown("### ℹ️ Sobre o Sistema")
    st.markdown("Desenvolvido para estudo acadêmico com **Streamlit** e **Microsoft Foundry**.")

# ==========================================
# INTERFACE PRINCIPAL DO CHAT
# ==========================================
st.title("🤖 ChatBot Acadêmico com RAG")
st.markdown("Faça perguntas gerais ou baseadas no documento enviado na barra lateral.")

# Validação prévia de segurança para a Chave de API
if not minha_chave:
    st.warning("⚠️ Por favor, insira a sua **Chave de API (API Key)** na barra lateral para habilitar o chat.")

# Container com borda estilizada nativa do Streamlit
chat_container = st.container(border=True)

with chat_container:
    if not st.session_state.messages:
        st.info("Nenhuma mensagem no histórico. Comece a conversar abaixo!")
        
    # Exibir histórico de mensagens anteriores
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Capturar nova entrada do usuário
if prompt := st.chat_input("Digite sua mensagem aqui..."):
    if not minha_chave:
        st.error("Você precisa informar a Chave de API na barra lateral antes de enviar mensagens.")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()

# Gerar resposta do assistente se a última mensagem foi do usuário
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    if minha_chave:
        with st.chat_message("assistant"):
            with st.spinner("Analisando e gerando resposta..."):
                try:
                    client = OpenAI(
                        api_key=minha_chave,
                        base_url=meu_endpoint
                    )
                    
                    system_instruction = (
                        "Você é um assistente acadêmico especialista, prestativo e objetivo."
                    )
                    if st.session_state.file_context:
                        system_instruction += (
                            f"\n\nContexto extraído do documento enviado pelo usuário:\n"
                            f"---------------------\n{st.session_state.file_context}\n---------------------\n"
                            f"Instrução: Utilize preferencialmente as informações acima para responder à pergunta do usuário, caso sejam relevantes."
                        )
                    
                    messages_payload = [{"role": "system", "content": system_instruction}]
                    
                    for m in st.session_state.messages[-10:]:
                        messages_payload.append({"role": m["role"], "content": m["content"]})
                    
                    response = client.chat.completions.create(
                        model=meu_modelo,
                        messages=messages_payload,
                        temperature=0.7,
                        max_tokens=1000
                    )
                    
                    assistant_response = response.choices[0].message.content
                    st.markdown(assistant_symbol := assistant_response)
                    
                    st.session_state.messages.append({"role": "assistant", "content": assistant_response})
                    
                except Exception as e:
                    error_message = f"Erro de comunicação com o Microsoft Foundry: {e}"
                    st.error(error_message)
                    st.session_state.messages.append({"role": "assistant", "content": error_message})
