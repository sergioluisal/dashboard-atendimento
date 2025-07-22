# 📋 Acompanhamento de Atendimento

Este projeto é uma aplicação interativa desenvolvida em **Streamlit** para análise de dados de ordens de serviço. Ele permite o upload de arquivos CSV ou Excel, visualização de métricas e gráficos, além da exportação dos dados filtrados.

## 🔧 Funcionalidades

- Upload de arquivos `.csv`, `.xls` ou `.xlsx`.
- Filtros interativos por:
  - Estado (UF)
  - Status da OS
  - Tipo de OS
  - Período de abertura da OS
- Indicadores principais:
  - Total de Ordens de Serviço
  - Percentual de SLA atendido
  - Duração média entre o primeiro atendimento e o fechamento
- Gráficos:
  - Barras por Status da OS
  - Pizza por Tipo de OS
  - Linha temporal com evolução da abertura das OS
- Exportação dos dados filtrados em `.csv` e `.xlsx`.

## 📁 Colunas necessárias

A aplicação espera que o dataset contenha, idealmente, as seguintes colunas:

- `OrdemDeServico`
- `NumeroSerie`
- `ComPeca`
- `TipoOS`
- `Municipio`
- `Uf`
- `StatusDaOS`
- `DataDeAbertura`
- `DataPrimeiroAtendimento`
- `DataDeFechamento`
- `SLADeSolucaoAtendido`
- `ObservacaoDoCliente`

> Caso alguma coluna esteja ausente, uma mensagem será exibida com a lista das colunas faltantes.

## ▶️ Como executar

1. Crie e ative um ambiente virtual (opcional, mas recomendado):

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

2. Instale as dependências:

```bash
pip install -r requirements_acompanhamento.txt
```

3. Execute a aplicação:

```bash
streamlit run nome_do_arquivo.py
```

Substitua `nome_do_arquivo.py` pelo nome do arquivo Python que contém o código da aplicação.

## 📦 Requisitos

As bibliotecas utilizadas estão listadas no arquivo `requirements_acompanhamento.txt`.

## 📌 Observações

- O sistema trata automaticamente arquivos codificados em diferentes formatos (`utf-8`, `latin-1`, `cp1252`, etc).
- Registros com valores de duração inválidos (negativos ou > 180 dias) são automaticamente excluídos da média.
