from Header import *
import Dynamics.quantum_utils as utils
# Librerías implícitas necesarias: numpy, scipy.linalg.expm, qiskit (QuantumCircuit, transpile, AerSimulator)

def magnetizacion_exacta(H, initial_state, ts, indices_medir, n_particles):
    """
    Calcula la evolución temporal exacta de la magnetización <Z_i> usando matrices.
    """
    # Generamos los operadores Z solo para los índices que queremos medir
    Z_ops = {idx: utils.Z_i(indice_objetivo=idx, n_particulas=n_particles) for idx in indices_medir}
    
    resultados = {idx: [] for idx in indices_medir}
    
    for curr_t in ts:
        # Evolución matricial (hbar = 1)
        U = expm(-1j * H * curr_t)
        estado_avanzado = U @ initial_state
        estado_avanzado_adj = estado_avanzado.conj().T
        
        # Calculamos el valor esperado para cada índice
        for idx in indices_medir:
            val = np.real(np.dot(estado_avanzado_adj, Z_ops[idx] @ estado_avanzado))
            resultados[idx].append(val.item() if hasattr(val, 'item') else val)
            
    return resultados

def H_ising_circuit(lattice, hs, Js, t, error, order=1):
    """
    Construye el circuito cuántico para e^{-i H t}.
    Utiliza cotas teóricas para estimar los pasos 'm' de Trotter.
    """
    n_particles = len(lattice["points"]) 
    coupling_map = lattice["coupling_map"]
    
    L = len(Js.items()) + n_particles
    
    E_max_campo = max([abs(h) for h in hs]) if hs else 0
    E_max_int = max([abs(j) for j in Js.values()]) if Js else 0
    E_scale = max(E_max_campo, E_max_int)
    
    fase_total = E_scale * t
    
    # Cálculo de pasos m
    if order == 1:
        m_float = (L**2 * fase_total**2) / error
        m = max(1, int(np.ceil(m_float)))
    elif order == 2:
        m_float = np.sqrt((L**3 * fase_total**3) / error)
        m = max(1, int(np.ceil(m_float)))
    else:
        raise ValueError("El orden de Trotter-Suzuki debe ser 1 o 2.")
        
    qc = QuantumCircuit(n_particles)
    dt = t / m  
    
    def apply_X(delta_t):
        for i in range(n_particles):
            theta_x = -2 * hs[i] * delta_t
            qc.rx(theta_x, i)
            
    def apply_ZZ(delta_t):
        for (idx1, idx2), J_val in Js.items():
            if [idx1, idx2] in coupling_map:
                control, target = idx1, idx2
            elif [idx2, idx1] in coupling_map:
                control, target = idx2, idx1
            else:
                continue 
            
            theta_z = -2 * J_val * delta_t
            qc.cx(control, target)
            qc.rz(theta_z, target)
            qc.cx(control, target)

    for j in range(m):
        if order == 1:
            apply_X(dt)
            apply_ZZ(dt)
        elif order == 2:
            apply_X(dt / 2)
            apply_ZZ(dt)
            apply_X(dt / 2)

    return qc

def magnetizacion_qiskit(lattice, hs, Js, config, ts, error, indices_medir, order=1, shots=1024):
    """
    Simula la evolución de la magnetización <Z_i> construyendo circuitos cuánticos.
    """
    n_particles = len(lattice["points"])
    simulador = AerSimulator()
    
    resultados = {idx: [] for idx in indices_medir}
    
    print(f"Simulando circuitos en Qiskit para {len(ts)} instantes de tiempo...")
    for curr_t in ts:
        qc_init = QuantumCircuit(n_particles)
        for i, bit in enumerate(config):
            if bit == 1:
                qc_init.x(i)
                
        qc_evol = H_ising_circuit(lattice, hs, Js, curr_t, error, order=order)
        qc_full = qc_init.compose(qc_evol)
        qc_full.measure_all()
            
        circuito_compilado = transpile(qc_full, simulador)
        resultado = simulador.run(circuito_compilado, shots=shots).result()
        conteos = resultado.get_counts()
        
        z_exp_instante = {idx: 0 for idx in indices_medir}
        
        for bitstring, conteo in conteos.items():
            for idx in indices_medir:
                bit_val = bitstring[-(idx + 1)] # Qiskit lee de derecha a izquierda
                z_exp_instante[idx] += conteo if bit_val == '0' else -conteo
                
        for idx in indices_medir:
            resultados[idx].append(z_exp_instante[idx] / shots)
            
    return resultados