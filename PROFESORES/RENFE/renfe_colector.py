import requests
from datetime import datetime
from math import radians, sin, cos, asin, sqrt

URL = "https://tiempo-real.largorecorrido.renfe.com/renfe-visor/flotaLD.json"
UMBRAL_KM = 5

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
    trenes_limpios = []
    for tren in datos.get("trenes", []):
        tren_parseado = parsear_tren(tren)
        if validacion_trenes(tren_parseado):
            trenes_limpios.append(tren_parseado)
    return trenes_limpios


# ALERTA DE DISTANCIA ENTRE TRENES

def distancia_km(lat1, lon1, lat2, lon2):
    """Distancia en km entre dos puntos (fórmula de Haversine)."""
    R = 6371  # radio medio de la Tierra en km
    phi1, phi2 = radians(lat1), radians(lat2)
    dphi = radians(lat2 - lat1)
    dlambda = radians(lon2 - lon1)
    a = sin(dphi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(dlambda / 2) ** 2
    return 2 * R * asin(sqrt(a))

def trenes_cercanos(trenes, umbral_km=UMBRAL_KM):
    """Devuelve los pares de trenes a menos de umbral_km, ordenados de menor a mayor distancia."""
    alertas = []
    for i in range(len(trenes)):
        for j in range(i + 1, len(trenes)):  # j > i: cada pareja se compara una sola vez
            a, b = trenes[i], trenes[j]
            d = distancia_km(a["latitud"], a["longitud"], b["latitud"], b["longitud"])
            # Se ignoran los convoyes acoplados: coordenadas idénticas y misma estación siguiente
            acoplados = (a["latitud"] == b["latitud"]
                         and a["longitud"] == b["longitud"]
                         and a["estacion_siguiente"] == b["estacion_siguiente"])
            if d < umbral_km and not acoplados:
                alertas.append((a, b, d))
    return sorted(alertas, key=lambda alerta: alerta[2])

def imprimir_alertas(alertas):
    if not alertas:
        print(f"Sin alertas: ningún par de trenes a menos de {UMBRAL_KM} km.")
        return
    print(f"ALERTA: {len(alertas)} pares de trenes a menos de {UMBRAL_KM} km\n")
    for a, b, d in alertas:
        print(f"  {d:.2f} km | {a['cod_comercial']} ({a['matricula']}) "
              f"<-> {b['cod_comercial']} ({b['matricula']})")

if __name__ == "__main__":
    try:
        trenes = limpiar_trenes()   # descarga desde la API de Renfe
        print(f"Trenes válidos: {len(trenes)}\n")
        imprimir_alertas(trenes_cercanos(trenes))
    except RuntimeError as e:
        print(f"Error: {e}")
