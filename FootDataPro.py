import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import poisson
import os
from groq import Groq
import requests

st.set_page_config(page_title="FootDataPro", layout="wide")

# ==========================================
# 0. INICIALIZACIÓN DE LA IA Y API DE CUOTAS GLOBAL
# ==========================================
try:
    cliente_ia = Groq(api_key=st.secrets["GROQ_API_KEY"])
    ia_activa = True
except Exception as e:
    cliente_ia = None
    ia_activa = False

def buscar_cuotas_reales(equipo_local, equipo_vis):
    """Busca cuotas reales en múltiples ligas del mundo usando The Odds API."""
    api_key = st.secrets.get("ODDS_API_KEY")
    if not api_key:
        return None
    
    deportes_a_buscar = [
        "soccer_epl", "soccer_spain_la_liga", "soccer_italy_serie_a", 
        "soccer_germany_bundesliga", "soccer_france_ligue_one", 
        "soccer_usa_mls", "soccer_copa_libertadores", "soccer_copa_sudamericana"
    ]
    
    for deporte in deportes_a_buscar:
        url = f"https://api.the-odds-api.com/v4/sports/{deporte}/odds"
        try:
            respuesta = requests.get(url, params={
                "apiKey": api_key, 
                "regions": "us,eu", 
                "markets": "h2h", 
                "oddsFormat": "decimal"
            }, timeout=3)
            
            if respuesta.status_code == 200:
                datos = respuesta.json()
                for partido in datos:
                    api_home = partido.get('home_team', '').lower()
                    api_away = partido.get('away_team', '').lower()
                    
                    palabra_local = equipo_local.split()[0].lower()
                    palabra_vis = equipo_vis.split()[0].lower()
                    
                    if palabra_local in api_home or palabra_vis in api_away:
                        if 'bookmakers' in partido and len(partido['bookmakers']) > 0:
                            return partido['bookmakers'][0]['markets'][0]['outcomes']
        except:
            continue
            
    return None


# ==========================================
# REPARACIÓN DE COLOR: BARRA LATERAL OSCURA
# ==========================================
st.markdown("""
<style>
    [data-testid="stSidebar"] {
        background-color: #0e1117 !important;
    }
    [data-testid="stSidebar"] * {
        color: #ffffff !important;
    }
    section[data-testid="stSidebar"] .css-ng1t4o {
        background-color: #0e1117 !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# BARRA LATERAL: FILTROS DE CAZADOR
# ==========================================
st.sidebar.markdown("<h2 style='color: #2ecc71;'>🎯 Cazador de Cuotas</h2>", unsafe_allow_html=True)
st.sidebar.markdown("Filtra la jornada para ver **solo** los partidos que cumplan tus reglas:")

filtro_local = st.sidebar.slider("Min. % Victoria Local", 0, 100, 0)
filtro_visit = st.sidebar.slider("Min. % Victoria Visitante", 0, 100, 0)
filtro_over_15 = st.sidebar.slider("Min. % +1.5 Goles", 0, 100, 0) 
filtro_over = st.sidebar.slider("Min. % +2.5 Goles", 0, 100, 0)
filtro_btts = st.sidebar.slider("Min. % Ambos Anotan", 0, 100, 0)

st.sidebar.markdown("---")
st.sidebar.info("💡 Si dejas un control en 0, la aplicación mostrará todos los partidos sin filtrar esa métrica.")

# ==========================================
# CEREBRO ANALÍTICO LOCAL (MOTOR INTELIGENTE)
# ==========================================
def generar_analisis_groq(local, visitante, prob_local, prob_empate, prob_visit, prob_over, prob_btts):
    favorito = local if prob_local > prob_visit else visitante
    max_prob = max(prob_local, prob_visit)
    
    if max_prob >= 60:
        tendencia = f"marcada superioridad del **{favorito}** ({max_prob}%), perfilándose como el claro dominador del encuentro."
        recomendacion = f"Victoria directa o Hándicap favorable para {favorito}."
    elif max_prob >= 45:
        tendencia = f"leve favoritismo para el **{favorito}** ({max_prob}%), aunque con resistencia esperada del rival."
        recomendacion = f"Doble oportunidad o victoria simple con resguardo."
    else:
        tendencia = f"alta paridad estadística; un choque sumamente cerrado con un {prob_empate}% de probabilidad de empate."
        recomendacion = f"Empate apuesta no válida (DNB) o pocos goles."

    goles_comentario = ""
    if prob_over >= 65:
        goles_comentario = f"Alta expectativa ofensiva con un {prob_over}% para la línea de +2.5 goles."
    elif prob_over <= 40:
        goles_comentario = f"Tendencia a un desarrollo táctico y cerrado, con un {round(100 - prob_over, 1)}% de probabilidades de ver -2.5 goles."
    else:
        goles_comentario = f"Ritmo de anotaciones moderado con un {prob_over}% en el mercado de +2.5."

    btts_comentario = f"La probabilidad de que ambos equipos marquen (BTTS) se sitúa en un {prob_btts}%."

    analisis_final = f"Análisis táctico: El duelo presenta {tendencia} {goles_comentario} {btts_comentario} Mercado sugerido con mayor valor estadístico: **{recomendacion}**."
    return analisis_final

# ==========================================
# BLOQUE DE ESTILOS Y FONDO
# ==========================================
st.markdown(
    """
    <style>
    .stApp {
        background-image: linear-gradient(rgba(13, 17, 23, 0.85), rgba(13, 17, 23, 0.85)), url("https://raw.githubusercontent.com/DepPrediGol/FootDataPro/main/FootDataPro.jpg") !important;
        background-size: cover !important;
        background-position: center !important;
        background-repeat: no-repeat !important;
        background-attachment: fixed !important;
    }
    h1, h2, h3, h4, h5, h6, p, label, .stMarkdown, .stText {
        color: #ffffff !important;
    }
    [data-testid="stHeader"] {
        background-color: transparent !important;
    }
    [data-testid="stFileUploader"] {
        background-color: rgba(22, 27, 34, 0.95) !important;
        padding: 20px !important;
        border-radius: 14px !important;
        border: 2px dashed rgba(46, 204, 113, 0.6) !important;
    }
    [data-testid="stFileUploader"] button {
        background-color: #2ecc71 !important;
        color: #ffffff !important;
        font-weight: bold !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 0.5rem 1rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ==========================================
# 1. BLOQUE DE FUNCIONES MATEMÁTICAS
# ==========================================
def calcular_probabilidades(xg_local, xg_vis):
    max_goles = 5
    prob_matriz = np.zeros((max_goles+1, max_goles+1))
    lista_marcadores = []
    
    for i in range(max_goles+1):
        for j in range(max_goles+1):
            prob = poisson.pmf(i, xg_local) * poisson.pmf(j, xg_vis)
            prob_matriz[i][j] = prob
            lista_marcadores.append((f"{i} - {j}", prob))
            
    prob_empate = np.trace(prob_matriz)
    prob_local = np.tril(prob_matriz, -1).sum()
    prob_vis = np.triu(prob_matriz, 1).sum()
    
    prob_over15 = sum(prob_matriz[i][j] for i in range(max_goles+1) for j in range(max_goles+1) if i+j > 1.5)
    prob_over25 = sum(prob_matriz[i][j] for i in range(max_goles+1) for j in range(max_goles+1) if i+j > 2.5)
    prob_btts_si = sum(prob_matriz[i][j] for i in range(1, max_goles+1) for j in range(1, max_goles+1))
    
    lista_marcadores.sort(key=lambda x: x[1], reverse=True)
    top_5 = [(marcador, f"{round(prob * 100, 1)}%") for marcador, prob in lista_marcadores[:5]]
    
    return {
        "Local %": round(prob_local * 100, 1), 
        "Empate %": round(prob_empate * 100, 1), 
        "Visitante %": round(prob_vis * 100, 1),
        "Over 1.5 %": round(prob_over15 * 100, 1), 
        "Over 2.5 %": round(prob_over25 * 100, 1), 
        "BTTS %": round(prob_btts_si * 100, 1),
        "Top 5 Marcadores": top_5
    }

def obtener_racha_detallada(df_partidos, es_local):
    df_recientes = df_partidos.head(10)
    if len(df_recientes) == 0:
        return "N/A", "Sin datos", 0.0
        
    goles_fav_col = 'Goles_Local' if es_local else 'Goles_Visitante'
    goles_con_col = 'Goles_Visitante' if es_local else 'Goles_Local'
    
    g = 0; e = 0; p = 0
    resultados_html = []
    goles_totales_fav = 0
    
    for index, fila in df_recientes.iterrows():
        gf = int(fila[goles_fav_col])
        gc = int(fila[goles_con_col])
        goles_totales_fav += gf
        marcador_str = f"{gf}-{gc}" if es_local else f"{gc}-{gf}"
            
        if gf > gc:
            g += 1
            resultados_html.append(f'<span style="background-color: rgba(46, 204, 113, 0.15); color: #2ecc71; padding: 2px 6px; border-radius: 4px; font-weight: bold; margin-right: 4px; font-size: 12px;">✅ {marcador_str}</span>')
        elif gf == gc:
            e += 1
            resultados_html.append(f'<span style="background-color: rgba(241, 196, 15, 0.15); color: #f39c12; padding: 2px 6px; border-radius: 4px; font-weight: bold; margin-right: 4px; font-size: 12px;">➖ {marcador_str}</span>')
        else:
            p += 1
            resultados_html.append(f'<span style="background-color: rgba(231, 76, 60, 0.15); color: #e74c3c; padding: 2px 6px; border-radius: 4px; font-weight: bold; margin-right: 4px; font-size: 12px;">❌ {marcador_str}</span>')
            
    return f"{g}G - {e}E - {p}P", "".join(resultados_html), round(goles_totales_fav / len(df_recientes), 2)

def obtener_top_4_fijas(lista_predicciones_jornada):
    candidatas = []
    for item in lista_predicciones_jornada:
        local = item['local']
        vis = item['vis']
        p = item['probs']
        
        if p['Local %'] >= 55:
            candidatas.append({
                'partido': f"{local} vs {vis}", 
                'tipo': 'Victoria Local', 
                'valor': p['Local %'], 
                'razón': f"El equipo local presenta una tendencia estadística de victoria del {p['Local %']}% basada en su rendimiento histórico de local."
            })
        elif p['Visitante %'] >= 50:
            candidatas.append({
                'partido': f"{local} vs {vis}", 
                'tipo': 'Victoria Visitante', 
                'valor': p['Visitante %'], 
                'razón': f"Superioridad visitante del {p['Visitante %']}% fundamentada en su desempeño reciente fuera de casa."
            })
        if p['Over 2.5 %'] >= 65:
            candidatas.append({
                'partido': f"{local} vs {vis}", 
                'tipo': 'Más de 2.5 Goles (+2.5)', 
                'valor': p['Over 2.5 %'], 
                'razón': f"Alta expectativa de anotaciones con un {p['Over 2.5 %']}% de probabilidad de superar la línea de 2.5 goles en el global del encuentro."
            })
        if p['BTTS %'] >= 65:
            candidatas.append({
                'partido': f"{local} vs {vis}", 
                'tipo': 'Ambos Anotan (BTTS Sí)', 
                'valor': p['BTTS %'], 
                'razón': f"La matriz de Poisson refleja un índice de {p['BTTS %']}% de probabilidad de que ambos equipos consigan vulnerar la portería contraria."
            })

    candidatas.sort(key=lambda x: x['valor'], reverse=True)
    return candidatas[:4]

# ==========================================
# 2. INTERFAZ Y CARGA DE ARCHIVOS
# ==========================================
st.markdown("""
<div style="background: linear-gradient(135deg, rgba(46, 204, 113, 0.15) 0%, rgba(52, 152, 219, 0.15) 100%); padding: 20px; border-radius: 12px; border: 1px solid rgba(150, 150, 150, 0.2); margin-bottom: 20px;">
    <h2 style="margin: 0; color: #2ecc71;">⚽ FootDataPro </h2>
    <p style="margin: 5px 0 0 0; opacity: 0.85; font-size: 15px;">
        Sistema inteligente automatizado por bloques de Poisson y análisis en tiempo real.
    </p>
</div>
""", unsafe_allow_html=True)

archivos_csv = st.file_uploader("📂 Adjunta tus bases de datos (.csv)", type=["csv"], accept_multiple_files=True)

if archivos_csv:
    st.markdown("---")
    nombres_ligas = [archivo.name.replace(".csv", "").upper() for archivo in archivos_csv]
    pestañas = st.tabs(nombres_ligas)
    
    partidos_analizados_total = 0
    
    for archivo, pestaña in zip(archivos_csv, pestañas):
        with pestaña:
            df = pd.read_csv(archivo)
            nombre_liga = archivo.name.replace(".csv", "").upper()
            
            columnas_req = ['home_team', 'away_team', 'result', 'status']
            if not all(col in df.columns for col in columnas_req):
                st.error(f"⚠️ El archivo {archivo.name} no tiene las columnas requeridas.")
                continue
                
            df['status_clean'] = df['status'].astype(str).str.strip().str.capitalize()
            df_jugados = df[df['status_clean'] == 'Final'].copy()
            df_proximos = df[df['status_clean'] != 'Final'].copy()
            
            df_jugados = df_jugados[df_jugados['result'].str.contains('-')] 
            df_jugados[['Goles_Local', 'Goles_Visitante']] = df_jugados['result'].str.split('-', expand=True).astype(float)
            
            if 'date' in df.columns and 'matchday' in df.columns:
                df['date_parsed_full'] = pd.to_datetime(df['date'], format='%d/%m/%Y', errors='coerce')
                df_pendientes = df[df['status'].astype(str).str.strip().str.capitalize() != 'Final'].copy()
                hoy = pd.Timestamp.now().normalize()
                df_proximos_reales = df_pendientes[df_pendientes['date_parsed_full'] >= hoy].sort_values('date_parsed_full')
                
                if not df_proximos_reales.empty:
                    df_proximos_reales['matchday_clean'] = pd.to_numeric(df_proximos_reales['matchday'], errors='coerce')
                    jornada_actual = df_proximos_reales.iloc[0]['matchday_clean']
                    df_solo_jornada_siguiente = df[
                        (pd.to_numeric(df['matchday'], errors='coerce') == jornada_actual) & 
                        (df['status'].astype(str).str.strip().str.capitalize() != 'Final')
                    ].copy()
                else:
                    df_solo_jornada_siguiente = df_proximos.head(10)
            else:
                df_solo_jornada_siguiente = df_proximos.head(10)
            
            if len(df_solo_jornada_siguiente) == 0:
                st.warning(f"No se detectaron partidos próximos para {nombre_liga}.")
                continue

            lista_apuestas_liga = []

            for index, fila in df_solo_jornada_siguiente.iterrows():
                equipo_local = fila['home_team']
                equipo_visitante = fila['away_team']
                
                fecha = str(fila.get('date', ''))
                hora = str(fila.get('time', ''))
                texto_fecha_hora = ""
                if fecha != "nan" and fecha.strip() != "":
                    texto_fecha_hora += f" 📅 {fecha}"
                if hora != "nan" and hora.strip() != "":
                    texto_fecha_hora += f" ⏰ {hora}"
                
                df_local_todos = df_jugados[df_jugados['home_team'] == equipo_local]
                df_vis_todos = df_jugados[df_jugados['away_team'] == equipo_visitante]
                
                if len(df_local_todos) > 0 and len(df_vis_todos) > 0:
                    xg_local = df_local_todos['Goles_Local'].mean()
                    xg_visitante = df_vis_todos['Goles_Visitante'].mean()
                    probs = calcular_probabilidades(xg_local, xg_visitante)
                    
                    if (probs['Local %'] < filtro_local or 
                        probs['Visitante %'] < filtro_visit or
                        probs['Over 1.5 %'] < filtro_over_15 or 
                        probs['Over 2.5 %'] < filtro_over or 
                        probs['BTTS %'] < filtro_btts):
                        continue
                        
                    partidos_analizados_total += 1
                    
                    with st.container(border=True):
                        st.markdown(f"<h3 style='color: #3498db; margin-top: 0; margin-bottom: 20px;'>⚽ {equipo_local} vs {equipo_visitante} <span style='font-size: 15px; color: #bdc3c7; font-weight: 500; margin-left: 12px;'>{texto_fecha_hora}</span></h3>", unsafe_allow_html=True)
                        
                        lista_apuestas_liga.append({
                            "local": equipo_local,
                            "vis": equipo_visitante,
                            "probs": probs
                        })
                        
                        racha_loc, marcadores_loc, prom_loc = obtener_racha_detallada(df_local_todos, es_local=True)
                        racha_vis, marcadores_vis, prom_vis = obtener_racha_detallada(df_vis_todos, es_local=False)
                        
                        col_r1, col_r2 = st.columns(2)
                        with col_r1:
                            st.markdown(f"""
                            <div style="background-color: rgba(46, 204, 113, 0.05); border-left: 4px solid #2ecc71; padding: 12px; border-radius: 0 8px 8px 0;">
                                🏠 <b>Local: {equipo_local}</b><br>
                                <b>Racha (10 PJ):</b> {racha_loc}<br>
                                <div style="margin-top: 6px; margin-bottom: 6px;"><b>Marcadores:</b><br>{marcadores_loc}</div>
                                <b>Promedio Goles Anotados:</b> {prom_loc} por partido
                            </div>
                            """, unsafe_allow_html=True)
                            
                        with col_r2:
                            st.markdown(f"""
                            <div style="background-color: rgba(52, 152, 219, 0.05); border-left: 4px solid #3498db; padding: 12px; border-radius: 0 8px 8px 0;">
                                ✈️ <b>Visitante: {equipo_visitante}</b><br>
                                <b>Racha (10 PJ):</b> {racha_vis}<br>
                                <div style="margin-top: 6px; margin-bottom: 6px;"><b>Marcadores:</b><br>{marcadores_vis}</div>
                                <b>Promedio Goles Anotados:</b> {prom_vis} por partido
                            </div>
                            """, unsafe_allow_html=True)
                            
                        st.write("") 
                        st.write("**Probabilidades Generales (Basado en el total del historial)**")
                        p_col1, p_col2, p_col3, p_col4, p_col5, p_col6 = st.columns(6)
                        
                        metricas_datos = [
                            ("🏠 Local", f"{probs['Local %']}%", p_col1),
                            ("🤝 Empate", f"{probs['Empate %']}%", p_col2),
                            ("✈️ Visitante", f"{probs['Visitante %']}%", p_col3),
                            ("📈 Over 1.5", f"{probs['Over 1.5 %']}%", p_col4),
                            ("⚽ Over 2.5", f"{probs['Over 2.5 %']}%", p_col5),
                            ("🥅 BTTS", f"{probs['BTTS %']}%", p_col6)
                        ]
                        
                        for etiqueta, valor, columna in metricas_datos:
                            with columna:
                                st.markdown(f"""
                                <div style="text-align: center; padding: 8px; border-radius: 8px; background-color: rgba(100, 100, 100, 0.08); border: 1px solid rgba(150, 150, 150, 0.15);">
                                    <div style="font-size: 12px; font-weight: 600; opacity: 0.8;">{etiqueta}</div>
                                    <div style="font-size: 18px; font-weight: bold; margin-top: 4px;">{valor}</div>
                                </div>
                                """, unsafe_allow_html=True)
                        
                        st.write("")
                        
                        # ==========================================
                        # 💎 COMPARATIVA DE CUOTAS JUSTAS VS API
                        # ==========================================
                        st.write("⚖️ **Comparativa: Cuota Justa vs. Cuota Real de la API**")
                        cuotas_api = buscar_cuotas_reales(equipo_local, equipo_visitante)
                        
                        cj_col1, cj_col2, cj_col3, cj_col4, cj_col5, cj_col6, cj_col7 = st.columns(7)
                        
                        def cuota_justa(prob):
                            return round(100 / prob, 2) if prob > 0 else 0.00
                            
                        prob_btts_no = 100 - probs['BTTS %']
                        
                        cuotas_datos = [
                            ("Local", cuota_justa(probs['Local %']), cj_col1),
                            ("Empate", cuota_justa(probs['Empate %']), cj_col2),
                            ("Visitante", cuota_justa(probs['Visitante %']), cj_col3),
                            ("+1.5", cuota_justa(probs['Over 1.5 %']), cj_col4),
                            ("+2.5", cuota_justa(probs['Over 2.5 %']), cj_col5),
                            ("BTTS Sí", cuota_justa(probs['BTTS %']), cj_col6),
                            ("BTTS No", cuota_justa(prob_btts_no), cj_col7)
                        ]
                        
                        for etiqueta, cuota, columna in cuotas_datos:
                            with columna:
                                color_borde = "rgba(241, 196, 15, 0.6)"
                                fondo = "rgba(241, 196, 15, 0.05)"
                                texto_extra = ""
                                
                                if cuotas_api:
                                    cuota_real = None
                                    for outcome in cuotas_api:
                                        nombre_out = outcome.get('name', '').lower()
                                        
                                        if etiqueta == "Local" and equipo_local[:4].lower() in nombre_out:
                                            cuota_real = outcome['price']
                                        elif etiqueta == "Visitante" and equipo_visitante[:4].lower() in nombre_out:
                                            cuota_real = outcome['price']
                                        elif etiqueta == "Empate" and "draw" in nombre_out:
                                            cuota_real = outcome['price']
                                            
                                    if cuota_real:
                                        if cuota_real > cuota:
                                            color_borde = "#2ecc71"
                                            fondo = "rgba(46, 204, 113, 0.15)"
                                            texto_extra = f"<div style='font-size: 10px; color: #2ecc71; font-weight: bold;'>¡Valor! @{cuota_real}</div>"
                                        else:
                                            texto_extra = f"<div style='font-size: 10px; opacity: 0.7;'>Real: @{cuota_real}</div>"

                                st.markdown(f"""
                                <div style="text-align: center; padding: 6px; border-radius: 6px; background-color: {fondo}; border: 1px dashed {color_borde};">
                                    <div style="font-size: 11px; color: #f1c40f; font-weight: 600;">Cuota {etiqueta}</div>
                                    <div style="font-size: 17px; font-weight: bold; color: #f1c40f;">@{cuota}</div>
                                    {texto_extra}
                                </div>
                                """, unsafe_allow_html=True)
                        
                        st.write("")
                        st.write("🎯 **Top 5 Marcadores Exactos**")
                        tm1, tm2, tm3, tm4, tm5 = st.columns(5)
                        for i, (marcador, porcentaje) in enumerate(probs['Top 5 Marcadores']):
                            with [tm1, tm2, tm3, tm4, tm5][i]:
                                st.markdown(f"""
                                <div style="text-align: center; padding: 10px; border-radius: 8px; background-color: rgba(150, 150, 150, 0.1);">
                                    <span style="font-size: 26px; font-weight: bold;">{marcador}</span><br>
                                    <span style="font-size: 14px; opacity: 0.8;">{porcentaje}</span>
                                </div>
                                """, unsafe_allow_html=True)
                        
                        st.write("")
                        if ia_activa:
                            with st.spinner(f"🤖 La IA está analizando {equipo_local} vs {equipo_visitante}..."):
                                analisis_ia = generar_analisis_groq(equipo_local, equipo_visitante, probs['Local %'], probs['Empate %'], probs['Visitante %'], probs['Over 2.5 %'], probs['BTTS %'])
                            st.markdown(f"""
                            <div style="background-color: rgba(13, 17, 23, 0.95); border: 1px solid rgba(46, 204, 113, 0.5); border-left: 6px solid #2ecc71; border-radius: 8px; padding: 15px; margin-top: 15px;">
                                <div style="color: #2ecc71; font-weight: bold; font-size: 16px; margin-bottom: 8px;">🤖 ANÁLISIS DE IA EN VIVO</div>
                                <div style="color: #ffffff; font-size: 15px; line-height: 1.6;">{analisis_ia}</div>
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    st.error(f"No hay suficientes datos históricos para {equipo_local} o {equipo_visitante}.")
                
            if len(lista_apuestas_liga) > 0:
                top_fijas = obtener_top_4_fijas(lista_apuestas_liga)
                if top_fijas:
                    st.markdown("---")
                    st.subheader("🔥 Top 4 Predicciones Más Fijas de la Fecha")
                    cols_fijas = st.columns(2)
                    for idx, ap in enumerate(top_fijas):
                        with cols_fijas[idx % 2]:
                            st.markdown(f"""
                            <div style="border: 2px solid rgba(46, 204, 113, 0.4); background-color: rgba(46, 204, 113, 0.05); padding: 15px; border-radius: 10px; margin-bottom: 12px;">
                                <div style="font-size: 14px; font-weight: bold; color: #2ecc71; margin-bottom: 5px;">🎯 SELECCIÓN #{idx + 1} ({ap['valor']}%)</div>
                                <div style="font-size: 18px; font-weight: bold; margin-bottom: 8px;">{ap['partido']}</div>
                                <div style="font-size: 15px; font-weight: 600; color: #3498db;">👉 {ap['tipo']}</div>
                            </div>
                            """, unsafe_allow_html=True)