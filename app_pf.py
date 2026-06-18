# Bibliotecas_________________________________________________________________________

import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
import plotly.express as px
from shapely.geometry import LineString
from folium.plugins import MarkerCluster
from streamlit_folium import folium_static
import branca.colormap as cm

#Datos___________________________________________________________________________

st.title("Gestión de activos acueducto municipal de Dota")

#Carga de datos
URL_MEDIDORES = "medidores.csv"
URL_TUBERIAS = "Tuberias.csv"

@st.cache_data
def cargar_datos_medidores():
    """Carga los datos de medidores"""
    datos_medidores = pd.read_csv(
        URL_MEDIDORES,
        sep=";",
        decimal=","
    )

    datos_medidores.columns = datos_medidores.columns.str.strip()

    return datos_medidores

@st.cache_data
def cargar_datos_tuberias():
    """Carga los datos de tuberías."""
    datos_tuberias = pd.read_csv(
        URL_TUBERIAS,
        sep=";",
        decimal=","
    )
    datos_tuberias.columns = datos_tuberias.columns.str.strip()

    datos_tuberias["Longitud"] = pd.to_numeric(
        datos_tuberias["Longitud"].astype(str).str.replace(",", ".", regex=False),
        errors="coerce"
    )

    return datos_tuberias

# ----- Carga de datos -----
medidores = cargar_datos_medidores()
tuberias = cargar_datos_tuberias()

## Introducción y tabla_____________________________________________________________________________

st.markdown("""
El Departamento de Acueducto del municipio de Dota actualmente no contempla un
sistema para la gestión de activos de los sistemas de agua de las comunidades
que tiene a cargo. Dispone de levantamientos topográficos en algunos sectores,
pero no en su totalidad, lo que ha obstaculizado la adquisición de recursos y
financiamiento.

Dicha limitación en gestión hace que la **generación de inventarios, materiales
en stock y el desarrollo de presupuestos** se haga de forma empírica, al no
contar con información base.

En cuanto a funcionamiento, la captación del recurso se realiza por **nacientes
de agua**, conformando el sistema por la tubería de conducción hasta los tanques
de almacenamiento y brindar el servicio a los hogares mediante la tubería de
distribución. El acueducto contempla **macromedidores en nueve sectores,
válvulas, hidrantes y los micromedidores** en las tomas domiciliares. Disponen
de un sistema de búsqueda por número de medidor para realizar los cobros, el
cual se encarga una funcionaria del departamento para realizarlo. El acueducto
municipal brinda el servicio en el centro de *Santa María, El Jardín y Copey*.
""")

# Filtros interactivos__________________________________________________________________
#tuberias

st.sidebar.header("Filtros")

estados_tuberia = sorted(tuberias["Estado"].dropna().unique())
materiales_tuberia = sorted(tuberias["Material"].dropna().unique())

estado_seleccionado = st.sidebar.multiselect(
    "Estado de las tuberías",
    estados_tuberia,
    default=estados_tuberia
)
if not estado_seleccionado:
    st.warning("Seleccione al menos un estado de tubería para mostrar la información.")
    st.stop()

material_seleccionado = st.sidebar.multiselect(
    "Material de las tuberías",
    materiales_tuberia,
    default=materiales_tuberia
)

if not material_seleccionado:
    st.warning("Seleccione al menos un material de tubería para mostrar la información.")
    st.stop()

tuberias_filtradas = tuberias[
    (tuberias["Estado"].isin(estado_seleccionado)) &
    (tuberias["Material"].isin(material_seleccionado))
].copy()

#Medidores

# Filtro interactivo por estado de medidores
st.sidebar.header("Filtros")

estados_medidor = sorted(medidores["estado"].dropna().unique())

estado_medidor_seleccionado = st.sidebar.multiselect(
    "Estado de los medidores",
    estados_medidor,
    default=estados_medidor
)
if not estado_medidor_seleccionado:
    st.warning("Seleccione al menos un estado de medidor para mostrar la información.")
    st.stop()

medidores_filtrados = medidores[
    medidores["estado"].isin(estado_medidor_seleccionado)
].copy()
#__________________________________________________________________________
#Tabla
st.title("Datos medidores Dota")
estado_carga_medidores = st.text("Cargando datos de medidores...")

estado_carga_medidores.text("¡Datos de medidores cargados exitosamente!")

st.markdown("""
La siguiente tabla muestra información general de los medidores registrados,
incluyendo el *número de medidor, finca asociada, estado y fechas de instalación
y mantenimiento*.
""")

# Conformación de la tabla
columnas = [
    "#_medidor",
    "numero_fin",
    "estado",
    "fecha_mant",
    "fecha_inst"
]

datos_tabla = medidores_filtrados[columnas].copy()

# Convertir fechas formato día/mes/año
for columna_fecha in ["fecha_mant", "fecha_inst"]:

    fecha_original = datos_tabla[columna_fecha].astype(str).str.strip()

    fecha_convertida = pd.to_datetime(
        fecha_original,
        errors="coerce",
        dayfirst=True
    )

    datos_tabla[columna_fecha] = fecha_convertida.dt.strftime("%Y-%m-%d")
    datos_tabla.loc[fecha_convertida.isna(), columna_fecha] = fecha_original

# Renombrar columnas
columnas_espanol = {
    "#_medidor": "Medidor",
    "numero_fin": "Finca",
    "estado": "Estado",
    "fecha_mant": "Mantenimiento",
    "fecha_inst": "Instalación"
}

datos_tabla = datos_tabla.rename(columns=columnas_espanol)

# Renombrar columnas
columnas_espanol = {
    "#_medidor": "Medidor",
    "numero_fin": "Finca",
    "estado": "Estado",
    "fecha_mant": "Mantenimiento",
    "fecha_inst": "Instalación"
}

datos_tabla = datos_tabla.rename(columns=columnas_espanol)

st.subheader("Datos generales por medidor en Sector Rubén")

st.dataframe(datos_tabla, hide_index=True)    ##primer entregable##

st.markdown(""" Se observa un registro completo tanto de la ubicación en las fincas correspondientes
como en proporcionar información relacionada a la fecha de instalación y mantenimiento, necesarios para
determinar la vida útil del componente y analizar posibles cambios.""")

# Gráfico estadístico: longitud total de tuberías por material_____________________________

st.subheader("Longitud total de tuberías por material")

st.markdown(""" La información relevante para este componente radica en el tipo de material
que se utiliza dentro del sector y la longitud total, esto a fin de contemplar el cambio
de elementos por materiales de mayor resistencia.""")


# Agrupar por material
longitud_material = (
    tuberias_filtradas
    .groupby("Material", as_index=False)["Longitud"]
    .sum()
    .sort_values("Longitud", ascending=False)
)

# Crear gráfico con Plotly
if longitud_material.empty:
    st.warning("No hay datos para mostrar con los filtros seleccionados.")
else:
    fig_longitud = px.bar(
    longitud_material,
    x="Material",
    y="Longitud",
    color="Material",
    text="Longitud",
    title="Longitud total de tuberías por material",
    labels={
        "Material": "Material de la tubería",
        "Longitud": "Longitud total (m)"
    },
     color_discrete_map={
        "PVC": "#2E7D5B",
        "PEAD": "#2E597F"
    }
)
    fig_longitud.update_traces(
    texttemplate="%{y:.2f} m",
    hovertemplate=(
        "<b>Material:</b> %{x}<br>"
        "<b>Longitud total:</b> %{y:.2f} m"
        "<extra></extra>"
    )
)
# Formato del gráfico
    fig_longitud.update_layout(
        showlegend=False,
        height=420,
     margin=dict(l=20, r=20, t=20, b=20),
     plot_bgcolor="white",
     paper_bgcolor="white",
     yaxis=dict(
        title="Longitud total (m)",
        gridcolor="#E6EAF0",
        zeroline=False
    ),
    xaxis=dict(
        title="Material de la tubería"
    )
)

fig_longitud.update_yaxes(
    range=[0, longitud_material["Longitud"].max() * 1.15],
    tickformat=",.0f"
)


st.plotly_chart(fig_longitud, use_container_width=True)  ##segundo entregable##

st.markdown(""" Se observa un dominio del material **PVC** en la infraestructura de la tubería, por lo
que si se desea cambiar a PEAD, el resultado brinda el total a cambiar y que deberá contemplarse 
en el presupuesto del próximo año.""")

#____________________________________________________________

# Mapa combinado: medidores y tuberías
st.subheader("Mapa. Ubicación de medidores y tuberías")


# Crear GeoDataFrame de medidores en CRTM05
medidores_gdf = gpd.GeoDataFrame(
    medidores_filtrados,
    geometry=gpd.points_from_xy(
        medidores_filtrados["Longitud"],  # X / Este
        medidores_filtrados["Latitud"]    # Y / Norte
    ),
    crs="EPSG:5367"
)

# Crear geometría de líneas para tuberías en CRTM05
tuberias_filtradas["geometry"] = tuberias_filtradas.apply(
    lambda row: LineString([
        (row["Latitud1"], row["Longitud1"]),
        (row["Latitud2"], row["Longitud2"])
    ]),
    axis=1
)

tuberias_gdf = gpd.GeoDataFrame(
    tuberias_filtradas,
    geometry="geometry",
    crs="EPSG:5367"
)

# Convertir ambas capas a WGS84 para Folium
medidores_4326 = medidores_gdf.to_crs("EPSG:4326")
tuberias_4326 = tuberias_gdf.to_crs("EPSG:4326")

# Centro del mapa usando medidores
centro_lat = medidores_4326.geometry.y.mean()
centro_lon = medidores_4326.geometry.x.mean()

# Crear mapa base
mapa = folium.Map(
    location=[centro_lat, centro_lon],
    zoom_start=16,
    tiles="CartoDB positron"
)

# Grupo de tuberías
grupo_tuberias = folium.FeatureGroup(name="Tuberías")

for _, row in tuberias_4326.iterrows():

    if row["Estado"] == "Bueno":
        color = "green"
    elif row["Estado"] == "Regular":
        color = "orange"
    else:
        color = "red"

    popup_tuberia = f"""
    <b>ID tubería:</b> {row['FID']}<br>
    <b>Material:</b> {row['Material']}<br>
    <b>Estado:</b> {row['Estado']}<br>
    <b>Diámetro:</b> {row['Diam_mm']} mm<br>
    <b>Longitud:</b> {row['Longitud']} m<br>
    <b>Fecha mantenimiento:</b> {row['Fecha_mant']}<br>
    <b>Fecha instalación:</b> {row['Fecha_inst']}
    """

    coordenadas = [
        [lat, lon] for lon, lat in row.geometry.coords
    ]

    folium.PolyLine(
        locations=coordenadas,
        color=color,
        weight=4,
        opacity=0.8,
        popup=folium.Popup(popup_tuberia, max_width=300),
        tooltip=f"Tubería {row['FID']} - {row['Material']}"
    ).add_to(grupo_tuberias)

grupo_tuberias.add_to(mapa)

# Grupo de medidores
grupo_medidores = folium.FeatureGroup(name="Medidores")

for _, row in medidores_4326.iterrows():

    lat = row.geometry.y
    lon = row.geometry.x

    popup_medidor = f"""
    <b>Medidor:</b> {row['#_medidor']}<br>
    <b>Número finca:</b> {row['numero_fin']}<br>
    <b>Estado:</b> {row['estado']}<br>
    <b>Fecha instalación:</b> {row['fecha_inst']}<br>
    <b>Fecha mantenimiento:</b> {row['fecha_mant']}<br>
    <b>ID tubería:</b> {row['id_tuberia']}
    """

    folium.CircleMarker(
        location=[lat, lon],
        radius=5,
        popup=folium.Popup(popup_medidor, max_width=300),
        tooltip=f"Medidor {row['#_medidor']}",
        color="lightblue",
        fill=True,
        fill_color="blue",
        fill_opacity=0.8
    ).add_to(grupo_medidores)

grupo_medidores.add_to(mapa)

# Control para activar/desactivar capas
folium.LayerControl().add_to(mapa)

#Leyenda 

leyenda_tuberias = cm.StepColormap(
    colors=["green", "orange"],
   vmin=0,
   vmax=2,
    index=[0, 1, 2],
    caption="Estado de tuberías: Bueno | Regular "
)


leyenda_tuberias.width = 190
leyenda_tuberias.height = 40

# Quitar números de la barra
leyenda_tuberias.tick_labels = []

leyenda_tuberias.add_to(mapa)

# Mostrar mapa en Streamlit
folium_static(mapa, width=900, height=600)   ##tercer entregable##



st.markdown(""" La representación espacial de las tuberías en el mapa permite 
visualizar la estructura de la red de distribución y su relación con la
ubicación de los usuarios atendidos. Se observa una red continua que conecta 
los **distintos sectores del sistema**, permitiendo identificar la disposición de los 
tramos principales y secundarios. La distinción en color permite ver los sectores que 
requieren **mayor mantenimiento** al catalogarse en un estado regular, esto principalmente 
en la sección sobre "Calle Vieja", donde una longitud considerable requiere de mantenimiento.""")

st.markdown("""
_______________________________________________________________________________________________
""")
st.markdown("""
**Fuente de datos:** los datos utilizados corresponden a levantamientos
topográficos de medidores y tuberías del acueducto municipal de Dota,
así como de entrevistas a funcionarios del departamento correspondiente
realizadas en el 2023.
""")
