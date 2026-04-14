from Header import *

def interactions(puntos):
    """Crea un diccionario de interacciones ortogonales únicas."""
    mapa_indices = {punto: i for i, punto in enumerate(puntos, start=1)}
    num_puntos = len(puntos)
    interacciones = {i: [] for i in range(1, num_puntos + 1)}
    
    if not puntos:
        return interacciones
        
    D = len(puntos[0]) 
    for i, punto in enumerate(puntos, start=1):
        for dim in range(D):
            for delta in [-1, 1]:
                vecino = list(punto)
                vecino[dim] += delta
                vecino = tuple(vecino)
                if vecino in mapa_indices:
                    j = mapa_indices[vecino]
                    if i < j:
                        interacciones[i].append(j)
                        
    for i in interacciones:
        interacciones[i].sort()
    return interacciones

def get_Js(coupling_map: list, valor_J: float = 1.0):
    """
    Genera un diccionario de interacciones J para el modelo de Ising a partir de un coupling map.

    Args:
        coupling_map (list): El mapa de acoplamiento de la topología cuántica como lista de pares [origen, destino].
        valor_J (float): El valor constante de J a asignar a cada par de interacción. 
                         Por defecto es 1.0 (ferromagnético).

    Returns:
        dict: Un diccionario donde las claves son tuplas ordenadas (i, j) con i < j, 
              y los valores son la constante de interacción J.
    """
    interacciones_ising = {}

    # Ahora iteramos directamente sobre los pares [origen, destino] de la lista
    for origen, destino in coupling_map:
        # Ordenamos los índices de menor a mayor para asegurar la estructura (i, j) con i < j
        par = tuple(sorted((origen, destino)))
        
        # Solo añadimos el par si no lo hemos procesado previamente
        # (útil por si el coupling_map contiene enlaces bidireccionales explícitos)
        if par not in interacciones_ising:
            interacciones_ising[par] = valor_J
                
    return interacciones_ising