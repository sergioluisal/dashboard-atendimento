import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
import io

st.set_page_config(
    page_title="Acompanhamento de Atendimento",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

COLUNAS_DESEJADAS = [
    "OrdemDeServico",
    "NumeroSerie",
    "ComPeca",
    "TipoOS",
    "IdCliente"
    "Municipio",
    "Uf",
    "StatusDaOS",
    "DataDeAbertura",
    "DataPrimeiroAtendimento",
    "DataDeFechamento",
    "SLADeSolucaoAtendido",
    "ObservacaoDoCliente"
]

@st.cache_data
def load_data(uploaded_file):
    if uploaded_file is None:
        return pd.DataFrame()

    try:
        file_extension = uploaded_file.name.split(".")[-1].lower()
        if file_extension == "csv":
            encodings = ["utf-8", "latin-1", "iso-8859-1", "cp1252"]
            df = None
            for encoding in encodings:
                try:
                    df = pd.read_csv(uploaded_file, encoding=encoding, sep=";")
                    break
                except Exception:
                    uploaded_file.seek(0)
                    continue
            if df is None:
                st.error("Não foi possível decodificar o arquivo CSV.")
                return pd.DataFrame()
        elif file_extension in ["xls", "xlsx"]:
            df = pd.read_excel(uploaded_file)
        else:
            st.error("Formato de arquivo não suportado.")
            return pd.DataFrame()

        # Conversão de datas
        df["DataDeAbertura"] = pd.to_datetime(df["DataDeAbertura"], errors="coerce", dayfirst=True)
        df["DataDeFechamento"] = pd.to_datetime(df["DataDeFechamento"], errors="coerce", dayfirst=True)

        # Preencher apenas colunas que não sejam datetime
        for col in df.columns:
            if not np.issubdtype(df[col].dtype, np.datetime64):
                df[col] = df[col].fillna("Não informado")

        return df

    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

def safe_percentage(numerator, denominator):
    if denominator == 0 or pd.isna(denominator) or pd.isna(numerator):
        return 0
    return (numerator / denominator) * 100
    
def calculate_metrics(df):
    if df.empty:
        return {
            "total_os": 0,
            "sla_atendido": 0,
            "total_os_fechadas": 0,
            "percentual_fechadas": 0,
            "duracao_media": 0
        }

    total_os = len(df)

    # Lista de status que indicam fechamento
    status_fechados = [
    "fechada", "encerrada", "finalizada", "concluída", "concluido",
    "fechado", "resolvida", "finalizado", "encerrado", "concluido com sucesso",
    "fechada com sucesso", "concluído", "fechado com sucesso"]

    df["StatusDaOS_normalizado"] = df["StatusDaOS"].astype(str).str.strip().str.lower()
    total_os_fechadas = df[df["StatusDaOS_normalizado"].isin(status_fechados)].shape[0]
    df.drop(columns=["StatusDaOS_normalizado"], inplace=True)

    percentual_fechadas = (total_os_fechadas / total_os) * 100 if total_os > 0 else 0

    # Trata e converte a coluna de SLA
    sla_col = df["SLADeSolucaoAtendido"].astype(str).str.strip().replace({
        "Sim": 1,
        "Não": 0,
        "Não informado": np.nan,
        "nan": np.nan,
        "None": np.nan
    })
    sla_col = pd.to_numeric(sla_col, errors="coerce")
    sla_atendido = sla_col.mean() * 100 if not sla_col.isna().all() else 0

    # Converte datas
    for col in ["DataDeAbertura", "DataDeFechamento", "DataPrimeiroAtendimento"]:
        df[col] = pd.to_datetime(df[col], errors="coerce", dayfirst=True)

    # Cálculo da duração média com validação
    if "DataDeFechamento" in df.columns and "DataPrimeiroAtendimento" in df.columns:
        df["Duracao"] = (df["DataDeFechamento"] - df["DataPrimeiroAtendimento"]).dt.days
        df_valid = df[(df["Duracao"].notna()) & (df["Duracao"] >= 0) & (df["Duracao"] <= 180)]
        duracao_media = df_valid["Duracao"].mean()

        registros_excluidos = df[(df["Duracao"] < 0) | (df["Duracao"] > 180)]
        if not registros_excluidos.empty:
            st.warning(f"{len(registros_excluidos)} registros ignorados por conterem duração inválida.")
            with st.expander("Ver registros ignorados"):
                st.dataframe(registros_excluidos[["DataPrimeiroAtendimento", "DataDeFechamento", "Duracao"]])
    else:
        duracao_media = 0

    return {
        "total_os": total_os,
        "sla_atendido": sla_atendido,
        "total_os_fechadas": total_os_fechadas,
        "percentual_fechadas": percentual_fechadas,
        "duracao_media": duracao_media
    }

def create_bar_chart(df, x_col, title):
    if df.empty or x_col not in df.columns:
        fig = go.Figure()
        fig.add_annotation(text="Dados não disponíveis", x=0.5, y=0.5, showarrow=False)
        fig.update_layout(title=title, height=400)
        return fig

    counts = df[x_col].value_counts().head(10)
    fig = px.bar(x=counts.index, y=counts.values, labels={'x': x_col, 'y': 'Quantidade'}, title=title)
    fig.update_layout(height=400, showlegend=False)
    return fig

def create_pie_chart(df, col, title):
    if df.empty or col not in df.columns:
        fig = go.Figure()
        fig.add_annotation(text="Dados não disponíveis", x=0.5, y=0.5, showarrow=False)
        fig.update_layout(title=title, height=400)
        return fig

    counts = df[col].value_counts()
    fig = px.pie(values=counts.values, names=counts.index, title=title)
    fig.update_layout(height=400)
    return fig

def create_timeline_chart(df, date_col, title):
    if df.empty or date_col not in df.columns:
        fig = go.Figure()
        fig.add_annotation(text="Dados não disponíveis", x=0.5, y=0.5, showarrow=False)
        fig.update_layout(title=title, height=400)
        return fig

    df_valid = df[df[date_col].notna()].copy()
    df_valid["Mes"] = df_valid[date_col].dt.to_period('M').astype(str)
    monthly_counts = df_valid.groupby("Mes").size().reset_index(name="Quantidade")

    fig = px.line(monthly_counts, x="Mes", y="Quantidade", title=title, markers=True)
    fig.update_layout(height=400)
    return fig

# -------- INTERFACE --------
st.title("📋 Acompanhamento de Atendimento")
st.markdown("---")

uploaded_file = st.file_uploader("Faça upload do seu arquivo CSV ou Excel", type=["csv", "xls", "xlsx"])
df = load_data(uploaded_file)

if df is None or df.empty:
    st.info("Por favor, faça upload de um arquivo para começar.")
    st.stop()

# Mostrar os status únicos encontrados para análise
#if "StatusDaOS" in df.columns:
    #st.write("🛠️ Status únicos encontrados:", df["StatusDaOS"].dropna().unique())

st.sidebar.header("🔍 Filtros")
if "Uf" in df.columns:
    # Converte tudo para string
    estados = df["Uf"].dropna().apply(lambda x: str(x).strip())
    estados = ["Todos"] + sorted(estados.unique(), key=lambda x: (not str(x).isdigit(), str(x)))

    estado_sel = st.sidebar.selectbox("Estado:", estados)
    if estado_sel != "Todos":
        df = df[df["Uf"] == estado_sel]

if "StatusDaOS" in df.columns:
    status_options = ["Todos"] + sorted(df["StatusDaOS"].unique())
    status_sel = st.sidebar.selectbox("Status da OS:", status_options)
    if status_sel != "Todos":
        df = df[df["StatusDaOS"] == status_sel]

if "TipoOS" in df.columns:
    tipos_os = ["Todos"] + sorted(df["TipoOS"].unique())
    tipo_sel = st.sidebar.selectbox("Tipo de OS:", tipos_os)
    if tipo_sel != "Todos":
        df = df[df["TipoOS"] == tipo_sel]

if "DataDeAbertura" in df.columns:
    df = df[df["DataDeAbertura"].notna()]
    data_min = df["DataDeAbertura"].min().date()
    data_max = df["DataDeAbertura"].max().date()
    data_ini, data_fim = st.sidebar.date_input("Período de Abertura:", value=(data_min, data_max), min_value=data_min, max_value=data_max)
    df = df[(df["DataDeAbertura"].dt.date >= data_ini) & (df["DataDeAbertura"].dt.date <= data_fim)]

metrics = calculate_metrics(df)

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Total de OS", metrics["total_os"])
col2.metric("OS Fechadas", metrics["total_os_fechadas"])

# Lógica de cor e seta para percentual de OS fechadas
percentual = metrics["percentual_fechadas"]
if percentual >= 80:
    delta = "↑ Bom"
    delta_color = "normal"
elif percentual >= 50:
    delta = "→ Médio"
    delta_color = "off"
else:
    delta = "↓ Baixo"
    delta_color = "inverse"

col3.metric("Fechadas (%)", f"{percentual:.1f}%", delta=delta, delta_color=delta_color)
col4.metric("SLA Atendido", f"{metrics['sla_atendido']:.1f}%")
col5.metric("Duração Média", f"{metrics['duracao_media']:.1f} dias")


st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(create_bar_chart(df, "StatusDaOS", "OS por Status"), use_container_width=True)

with col2:
    st.plotly_chart(create_pie_chart(df, "TipoOS", "Distribuição por Tipo de OS"), use_container_width=True)

st.plotly_chart(create_timeline_chart(df, "DataDeAbertura", "Evolução de Abertura das OS"), use_container_width=True)

colunas_faltando = [col for col in COLUNAS_DESEJADAS if col not in df.columns]
if colunas_faltando:
    st.error(f"As seguintes colunas estão ausentes: {colunas_faltando}")
else:
    df_filtrado = df[COLUNAS_DESEJADAS]
    st.success("Colunas filtradas com sucesso!")
    st.markdown("### 📥 Exportar Dados")
    csv = df_filtrado.to_csv(index=False, sep=";")
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name=f"atendimento_filtrado_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )

    excel_buffer = io.BytesIO()
    df_filtrado.to_excel(excel_buffer, index=False, engine="openpyxl")
    excel_buffer.seek(0)
    st.download_button(
        label="Download Excel",
        data=excel_buffer,
        file_name=f"atendimento_filtrado_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
# Verifica se todas as colunas estão presentes
colunas_faltando = [col for col in COLUNAS_DESEJADAS if col not in df.columns]
if colunas_faltando:
    st.error(f"As seguintes colunas estão ausentes: {colunas_faltando}")
else:
    df_filtrado = df[COLUNAS_DESEJADAS]
    
    st.success("Colunas filtradas com sucesso!")
    st.subheader("✅ Dados filtrados:")
    st.dataframe(df_filtrado, use_container_width=True)
