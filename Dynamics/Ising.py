from Header import *
# Librerías implícitas necesarias: numpy (np), functools.reduce, qiskit.QuantumCircuit

def H_ising_matrix(lattice, hs, Js):
    """
    Construye la matriz del Hamiltoniano del modelo de Ising cuántico.
    En unidades adimensionales, 'hs' y 'Js' son valores relativos 
    (por ejemplo, respecto a la energía de interacción base J_0 = 1.0).
    """
    n_particles = len(lattice["points"]) 
    
    if len(hs) != n_particles:
        raise ValueError(f"El número de campos externos ({len(hs)}) debe coincidir con el número de partículas ({n_particles}).")
    
    dim_hilbert = 2 ** n_particles
    H = np.zeros((dim_hilbert, dim_hilbert), dtype='float64')
    
    # Definición de las matrices base locales
    I = np.eye(2)
    X = np.array([[0, 1], [1, 0]])
    Z = np.array([[1, 0], [0, -1]])
    
    # 1. Interacción con los campos externos (Término X_i)
    for idx in range(n_particles):
        ops = [I] * n_particles        
        ops[idx] = X                    
        
        # Término de energía adimensional
        term = -hs[idx] * reduce(np.kron, ops)
        H += term
        
    # 2. Interacciones de pares entre espines (Término Z_i Z_j)
    for (idx1, idx2), J_val in Js.items():
        ops = [I] * n_particles        
        ops[idx1] = Z                  
        ops[idx2] = Z                  
        
        # Término de energía adimensional
        term = -J_val * reduce(np.kron, ops)
        H += term

    return H

def get_lcu_components(n_particles, hs, Js):
    """
    Convierte los parámetros del modelo de Ising en listas preparadas para LCU.
    Separa el valor absoluto (coeficientes c_j) de los signos (fase global de U_j).
    """
    coeficientes = []
    unitarias = []

    # Términos del campo magnético: -h_i * X_i
    for i in range(n_particles):
        coeficientes.append(abs(hs[i]))
        qc_u = QuantumCircuit(n_particles)
        if -hs[i] < 0:
            qc_u.global_phase = np.pi 
        qc_u.x(i)
        unitarias.append(qc_u)

    # Términos de interacción: -J_ij * Z_i * Z_j
    for (i, j), J_link in Js.items():
        coeficientes.append(abs(J_link))
        qc_u = QuantumCircuit(n_particles)
        if -J_link < 0:
            qc_u.global_phase = np.pi
        qc_u.z(i)
        qc_u.z(j)
        unitarias.append(qc_u)

    return coeficientes, unitarias