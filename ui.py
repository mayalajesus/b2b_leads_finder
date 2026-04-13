import streamlit as st
import pandas as pd
from main import get_contact, dados_enriquecidos

# Configuração da página para ocupar a largura total
st.set_page_config(page_title="Lead Finder", page_icon="🙋", layout="wide")

st.title("🙋 Lead Extractor")
st.markdown("Busque leads qualificados e obtenha e-mails verificados em segundos.")

# Barra lateral para os filtros de busca
with st.sidebar:
    st.header("Configurações de Busca")
    job_title = st.text_input("Cargo", placeholder="Ex: Head of Marketing")
    location = st.text_input("Localização", placeholder="Ex: Salvador, Brazil")
    company = st.text_input("Empresa (Opcional)", placeholder="Ex: Google")
    
    st.divider()
    btn_buscar = st.button("Iniciar Busca", type="primary", use_container_width=True)

if btn_buscar:
    if not job_title:
        st.error("O campo 'Cargo' é obrigatório para iniciar a busca.")
    else:
        # feedback visual de progresso
        with st.status("Processando...", expanded=True) as status:
            # 1. Busca inicial
            st.write("🔍 Consultando base do Apollo...")
            raw_contacts = get_contact(job_title, location or None, company or None)
            
            if not raw_contacts:
                st.error("Nenhum contato básico encontrado com esses filtros.")
                status.update(label="Busca encerrada sem resultados.", state="error")
            else:
                st.write("🧬 Enriquecendo perfis e capturando e-mails...")
                # 2. Enriquecimento
                df_completo = dados_enriquecidos(raw_contacts)
                status.update(label="Processamento concluído!", state="complete", expanded=False)

                # --- VERIFICAÇÃO DE SEGURANÇA ---
                # Se a API retornou erro 422 ou bloqueou o enriquecimento, o DF estará vazio
                if df_completo.empty:
                    st.warning("⚠️ Os contatos foram encontrados, mas o Apollo bloqueou o acesso aos e-mails.")
                    st.info("Isso geralmente acontece quando os créditos de exportação da sua API Key acabaram.")
                else:
                    # Se chegamos aqui, temos dados para mostrar!
                    st.subheader(f"📊 {len(df_completo)} Leads Encontrados")
                    
                    # Botão de Download
                    csv = df_completo.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Baixar Planilha Completa (CSV)",
                        data=csv,
                        file_name=f"leads_{job_title.lower().replace(' ', '_')}.csv",
                        mime="text/csv",
                    )

                    # --- FILTRAGEM DE COLUNAS ---
                    # Selecionamos apenas as 5 colunas que você quer na tela
                    colunas_selecionadas = ["name", "job_title", "linkedin_url", "company", "email"]
                    
                    # Filtramos o DataFrame de visualização
                    df_view = df_completo[colunas_selecionadas]

                    # Exibição da Tabela
                    st.dataframe(
                        df_view,
                        column_config={
                            "name": st.column_config.TextColumn("Nome"),
                            "job_title": st.column_config.TextColumn("Cargo"),
                            "linkedin_url": st.column_config.LinkColumn("LinkedIn", display_text="Ver Perfil"),
                            "company": st.column_config.TextColumn("Empresa"),
                            "email": st.column_config.TextColumn("E-mail", width="large"),
                        },
                        width='stretch',
                        hide_index=True
                    )
else:
    st.info("Preencha o cargo e localização na barra lateral para começar.")