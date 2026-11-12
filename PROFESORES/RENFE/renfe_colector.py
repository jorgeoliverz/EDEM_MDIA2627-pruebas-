import requests
from datetime import datetime

URL = "https://tiempo-real.largorecorrido.renfe.com/renfe-visor/flotaLD.json"

#Descarga de los datos desde la API de Renfe y manejo de errores
def descargar_datos():
    try:
        response = requests.get(URL,timeout=10)
        response.raise_for_status()
        datos = response.json()
    except requests.RequestException as e:
        raise RuntimeError(f"Error de red o HTTP: {e}")
    except ValueError as e:
        raise RuntimeError(f"La respuesta no es un JSON válido: {e}")
    if not datos.get("trenes"):
        raise RuntimeError("Respuesta vacía")
    return datos

#Parseo del tren del JSON crudo a un diccionario con tipos limpios

def parsear_tren(tren: dict) -> dict:
    """Convierte un tren del JSON crudo en un diccionario con tipos limpios."""
    hora_llegada = tren.get("horaLlegadaSigEst")
    timestamp = tren.get("time")
    retraso = tren.get("ultRetraso")

    return {
        "cod_comercial": tren.get("codComercial"),
        "matricula": tren.get("mat"),
        "producto": tren.get("codProduct"),
        "origen": tren.get("codOrigen"),
        "destino": tren.get("codDestino"),
        "estacion_anterior": tren.get("codEstAnt"),
        "estacion_siguiente": tren.get("codEstSig"),
        "hora_llegada_sig_estacion": datetime.fromisoformat(hora_llegada) if hora_llegada else None,
        "retraso_min": int(retraso) if retraso not in (None, "") else None,
        "accesible": tren.get("accesible"),
        "plataforma": tren.get("p"),
        "latitud": tren.get("latitud"),
        "longitud": tren.get("longitud"),
        "timestamp": datetime.fromtimestamp(timestamp) if timestamp else None,
    }
    
#Validación de los datos del tren para asegurar que sean correctos y completos
def validacion_trenes(tren):
    lat = tren["latitud"]
    lon = tren["longitud"]
    if lat is None or lon is None:
        return False
    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        return False
    if lat == 0 and lon == 0:
        return False
    if not tren["matricula"] and not tren["cod_comercial"]:
        return False
    return True

def limpiar_trenes():
    """Descarga, parsea y valida los trenes, devolviendo una lista de trenes limpios."""
    datos = descargar_datos()
    trenes_limpios = {}
    for tren in datos.get("trenes", []):
        tren_parseado = parsear_tren(tren)
        if validacion_trenes(tren_parseado):
            trenes_limpios.append(tren_parseado)
    return trenes_limpios

