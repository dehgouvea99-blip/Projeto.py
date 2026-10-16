import streamlit as st
from openai import OpenAI
import PyPDF2
import io

# ==========================================
# CONFIGURAÇÕES DA API (MICROSOFT FOUNDRY)
# ==========================================
API_KEY = "6t2pTNsmNafDyo53MDAFIrvvQRBZXP7dLcr5j3TLxMS34LQVq3ZUJQQJ99CHACHYHv6XJ3w3AAAAACOGT7os"
MODEL_NAME = "gpt-4.1-mini"
# Endpoint padrão ajustado para a especificação v1 do Microsoft Foundry / Azure OpenAI
ENDPOINT = "https://marcelomaffeis-05082026-resource.services.ai.azure.com/openai/v1/"

# ==========================================
# CONFIGURAÇÃO DA PÁGINA E ESTILO VISUAL (CSS)
# ==========================================
st.set_page_config(
    page_title="ChatBot Acadêmico com RAG",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Estilização CSS customizada para bordas e refinamento estético
st.markdown("""
    <style>
    /* Estilo geral do fundo e fontes */
    .stApp {
        background-color: #f8f9fa;
    }
    
    /* Borda estilizada ao redor da área principal do chat */
    .chat-container-border {
        border: 2px solid #e2e8f0;
        border-radius: 12px;
        padding: 20px;
        background-color: #ffffff;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
        margin-bottom: 20px;
    }

    /* Ajustes na barra lateral */
    [data-testid="stSidebar"] {
        background-color: #f1f5f9;
        border-right: 1px solid #e2e8f0;
    }
    
    /* Títulos e cabeçalhos */
    h1 {
        color: #1e293b;
        font-weight: 700;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# BARRA LATERAL (UPLOAD DE ARQUIVOS / RAG)
# ==========================================
with st.sidebar:
    st.header("📂 Base de Conhecimento (RAG)")
    st.markdown("Envie um documento de referência (**PDF** ou **TXT**) para contextualizar as respostas do assistente.")
    
    uploaded_file = st.file_uploader("Escolha um arquivo", type=["pdf", "txt"])
    
    file_context = ""
    
    if uploaded_file is not None:
        file_extension = uploaded_file.name.split(".")[-1].lower()
        
        if file_extension == "pdf":
            try:
                reader = PyPDF2.PdfReader(uploaded_file)
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        file_context += text + "\n"
                st.success(f"PDF '{uploaded_file.name}' carregado com sucesso!")
            except Exception as e:
                st.error(f"Erro ao ler o arquivo PDF: {e}")
                
        elif file_extension == "txt":
            try:
                file_context = uploaded_file.read().decode("utf-8")
                st.success(f"TXT '{uploaded_file.name}' carregado com sucesso!")
            except Exception as e:
                st.error(f"Erro ao ler o arquivo TXT: {e}")
                
        if file_context:
            st.info(f"Contexto ativo: ~{len(file_context)} caracteres carregados.")
            
    st.markdown("---")
    st.markdown("### ℹ️ Sobre o Sistema")
    st.markdown("Desenvolvido para estudo acadêmico utilizando **Streamlit** e modelos hospedados na plataforma **Microsoft Foundry**.")

# ==========================================
# INTERFACE PRINCIPAL DO CHAT
# ==========================================
st.title("🤖 ChatBot Acadêmico com RAG")
st.markdown("Faça perguntas gerais ou baseadas no documento enviado na barra lateral.")

# Inicializar o histórico de conversas no session_state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Container principal com borda estilizada
st.markdown('<div class="chat-container-border">', unsafe_allow_html=True)

# Exibir histórico de mensagens anteriores
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

st.markdown('</div>', unsafe_allow_html=True)

# Capturar nova entrada do usuário
if prompt := st.chat_input("Digite sua mensagem aqui..."):
    # Salvar e exibir a mensagem do usuário
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Gerar resposta do assistente usando a API do Microsoft Foundry
    with st.chat_message("assistant"):
        with st.spinner("Analisando e gerando resposta..."):
            try:
                # Inicializar o cliente OpenAI com as credenciais do Microsoft Foundry
                client = OpenAI(
                    api_key=API_KEY,
                    base_url=ENDPOINT
                )
                
                # Construir o prompt do sistema injetando o contexto RAG (se houver arquivo)
                system_instruction = (
                    "Você é um assistente acadêmico especialista, prestativo e objetivo."
                )
                if file_context:
                    system_instruction += (
                        f"\n\nContexto extraído do documento enviado pelo usuário:\n"
                        f"---------------------\n{file_context}\n---------------------\n"
                        f"Instrução: Utilize preferencialmente as informações acima para responder à pergunta do usuário, caso sejam relevantes."
                    )
                
                # Montar o payload de mensagens para a API
                messages_payload = [{"role": "system", "content": system_instruction}]
                
                # Adicionar o histórico recente da conversa (últimas 10 interações)
                for m in st.session_state.messages[-10:]:
                    messages_payload.append({"role": m["role"], "content": m["content"]})
                
                # Chamada de API para o modelo configurado
                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=messages_payload,
                    temperature=0.7,
                    max_tokens=1000
                )
                
                assistant_response = response.choices[0].message.content
                st.markdown(assistant_response)
                
                # Salvar resposta no session_state
                st.session_state.messages.append({"role": "assistant", "content": assistant_response})
                
            except Exception as e:
                error_message = f"Erro de comunicação com o Microsoft Foundry: {e}"
                st.error(error_message)
                st.session_state.messages.append({"role": "assistant", "content": error_message})
