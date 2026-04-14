from Header import *

# Pauli matrices appearing in the Ising model
I = np.array([[1, 0],[0, 1]], dtype='float64')
X = np.array([[0, 1],[1, 0]], dtype='float64')
Z = np.array([[1, 0],[0, -1]], dtype='float64')

def Z_i(indice_objetivo, n_particulas):
    """
    Construye la matriz gigante para un operador que actúa sobre una sola partícula.
    Ejemplo para Z_2: I ⊗ Z ⊗ I ⊗ ... ⊗ I
    
    - op_local: La matriz 2x2 a aplicar (ej. Z o X)
    - indice_objetivo: La partícula sobre la que actúa (numerada desde 1)
    - n_particulas: Número total de partículas (N)
    """    
    # 1. Definimos el operador para la primera partícula
    if indice_objetivo == 0:
        operador_total = Z
    else:
        operador_total = I
        
    # 2. Hacemos el producto de Kronecker para el resto de partículas
    for i in range(1, n_particulas):
        if i == indice_objetivo:
            operador_total = np.kron(operador_total, Z)
        else:
            operador_total = np.kron(operador_total, I)
            
    return operador_total
    
def generar_estado_base(configuracion):
    """
    Genera un vector de estado cuántico normalizado para N partículas.
    'configuracion' es una lista de 0s (Up) y 1s (Down).
    Ejemplo: [0, 1, 0] genera el estado |0> ⊗ |1> ⊗ |0>
    """
    # 1. Definimos los estados individuales en base Z (tipo float64 para evitar problemas)
    up = np.array([1, 0], dtype='float64')   # |0>
    down = np.array([0, 1], dtype='float64') # |1>
    
    # 2. Inicializamos el estado total con la primera partícula
    estado_total = up if configuracion[0] == 0 else down
    
    # 3. Hacemos el producto de Kronecker iterativamente para el resto de partículas
    for spin in configuracion[1:]:
        estado_actual = up if spin == 0 else down
        estado_total = np.kron(estado_total, estado_actual)
        
    # 4. Normalizamos el vector (la suma de los cuadrados de sus amplitudes debe ser 1)
    # Aunque los estados base puros ya tienen norma 1, esta línea es vital
    # si luego empezamos a sumar estados para hacer superposiciones.
    norma = np.linalg.norm(estado_total)
    estado_normalizado = estado_total / norma
    
    return estado_normalizado