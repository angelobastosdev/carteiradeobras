import pandas as pd
import folium
import streamlit as st
import streamlit.components.v1 as components
from folium.plugins import Draw
from geopy.distance import geodesic

st.set_page_config(layout='wide')

# Ler o arquivo Excel
try:
    df = pd.read_excel("CARTEIRA.xlsx")
except Exception as e:
    st.error(f"Erro ao ler o arquivo Excel: {e}")
    st.stop()

# Remover espaços extras nos nomes das colunas
df.columns = df.columns.str.strip()

# Verificar os nomes das colunas para garantir que a coluna 'descricao_medida' existe
if 'descricao_medida' not in df.columns:
    st.error("A coluna 'descricao_medida' não foi encontrada no DataFrame.")
    st.stop()

# Obter as opções únicas de coordenadores (ou coordenação) para o dropdown
coordenacoes = df['Coordenação'].unique()

# Função para calcular a distância entre dois pontos (latitude, longitude)
def calcular_distancia(ponto1, ponto2):
    return geodesic(ponto1, ponto2).km  # Distância em quilômetros

# Função para criar o mapa baseado na coordenação selecionada
def criar_mapa(coord_selecionada, eventos_selecionados):
    # Filtrar o DataFrame com a coordenação escolhida
    df_filtrado = df[df['Coordenação'] == coord_selecionada]

    # Filtrar também pela 'descricao_medida' se algum evento for selecionado
    if eventos_selecionados:
        df_filtrado = df_filtrado[df_filtrado['descricao_medida'].isin(eventos_selecionados)]

    # Filtrar linhas com coordenadas não nulas
    df_filtrado = df_filtrado.dropna(subset=['Coordenadas'])

    # Calcular a latitude e longitude médias das coordenadas no dataframe filtrado
    lat_media = df_filtrado['Coordenadas'].apply(lambda x: float(x.split(',')[0])).mean()
    lon_media = df_filtrado['Coordenadas'].apply(lambda x: float(x.split(',')[1])).mean()

    # Criar o mapa centrado na média das coordenadas
    mapa = folium.Map(
        location=[lat_media, lon_media], 
        zoom_start=7, 
        control_scale=True,  # Habilitar controle de escala
        tiles='OpenStreetMap'  # Usar apenas OpenStreetMap
    )

    # Definir mapeamento de cores para os diferentes valores de descricao_medida
    cores_evento = {
        'OBRA EM CARTEIRA': 'blue',
        'OBRA PROGRAMADA': 'green',
        'REPROGRAMAR OBRA': 'yellow',
        'Evento 4': 'red',
        'Evento 5': 'purple'
    }

    # Adicionar marcadores no mapa
    for _, row in df_filtrado.iterrows():
        coordenada_str = row['Coordenadas']
        
        # Verifica se a coordenada não é NaN
        if pd.notna(coordenada_str):
            try:
                coordenada = tuple(map(float, coordenada_str.split(',')))  # Divide e converte para float
                numero_da_nota = row['Núm. Nota/Obra']
                descricao_medida = row['descricao_medida']
                quant_postes = row['Qde Poste']

                # Selecionar a cor do ícone com base na descrição do evento
                cor_evento = cores_evento.get(descricao_medida, 'gray')  # Cor padrão é cinza, caso não exista no mapeamento

                # Criar um conteúdo de popup com informações adicionais
                popup_conteudo = f"""
                    <strong>Número da Nota:</strong> {numero_da_nota}<br>
                    <strong>Descrição do Evento:</strong> {descricao_medida}<br>
                    <strong>Postes:</strong> {quant_postes}<br>
                """

                # Adiciona marcador no mapa com a cor do ícone definida
                folium.Marker(
                    location=coordenada,
                    popup=popup_conteudo,  # Exibir informações no popup
                    icon=folium.Icon(color=cor_evento)  # Cor do ícone conforme o evento
                ).add_to(mapa)
            except Exception as e:
                print(f"Erro ao processar coordenada: {coordenada_str}. Erro: {e}")
    
    # Adicionar funcionalidade de desenho para selecionar dois pontos no mapa
    draw = Draw(export=True)
    draw.add_to(mapa)

    # Exibir o mapa no formato HTML para o Streamlit
    mapa_html = mapa._repr_html_()
    
    return mapa_html

# Título do aplicativo Streamlit
st.title("CARTEIRA DE OBRAS")

# Criar o dropdown para seleção da coordenação
coord_selecionada = st.sidebar.selectbox("Selecione uma Coordenação", coordenacoes)

# Filtrar as opções da 'descricao_medida' com base na coordenação selecionada
eventos_filtrados = df[df['Coordenação'] == coord_selecionada]['descricao_medida'].unique()

# Criar o multiselect para filtrar os eventos
eventos_selecionados = st.sidebar.multiselect(
    "Selecione a(s) Descrição do Evento atribuída(s) à obra", 
    eventos_filtrados.tolist(), 
    default=eventos_filtrados.tolist()  # Por padrão, selecionar todos os eventos
)

# Criar o mapa com base na seleção
mapa_html = criar_mapa(coord_selecionada, eventos_selecionados)

# Exibir o mapa no Streamlit com o CSS ajustado
components.html(mapa_html, height=1000)

# Verificar linhas com coordenadas ausentes
df_sem_coordenadas = df[pd.isna(df['Coordenadas'])]

# Mostrar o DataFrame com linhas sem coordenadas no Streamlit
if not df_sem_coordenadas.empty:
    st.warning("Existem linhas sem coordenadas!")
    st.dataframe(df_sem_coordenadas)
