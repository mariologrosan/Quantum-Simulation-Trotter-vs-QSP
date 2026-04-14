from Header import *
# Librerías implícitas necesarias: numpy, qiskit (QuantumCircuit), qiskit.circuit.library.StatePreparation

def build_prep_circuit(coeficientes):
    """
    Construye el oráculo PREP denso para el método LCU.
    
    Args:
        coeficientes (list): Lista de los coeficientes c_j (deben ser > 0).
        
    Returns:
        QuantumCircuit: Circuito de n qubits que implementa PREP_dense.
    """
    k = len(coeficientes)
    n = int(np.ceil(np.log2(k))) if k > 1 else 1
    suma_c = sum(coeficientes)
    
    amplitudes = np.zeros(2**n, dtype=float)
    amplitudes[0] = np.sqrt(coeficientes[0] / suma_c)
    
    for j in range(1, k):
        amplitudes[j] = -np.sqrt(coeficientes[j] / suma_c)
        
    prep_gate = StatePreparation(amplitudes)
    qc_prep = QuantumCircuit(n, name="PREP")
    qc_prep.append(prep_gate, range(n))
    
    return qc_prep

def build_select_circuit(unitarias):
    """
    Construye el oráculo SELECT para la combinación lineal.
    
    Args:
        unitarias (list de QuantumCircuit): Lista de las k unitarias U_j.
                                            Todas deben tener el mismo número de qubits.
                                            
    Returns:
        QuantumCircuit: Circuito conjunto de (n ancillas + sys_qubits).
    """
    k = len(unitarias)
    n = int(np.ceil(np.log2(k))) if k > 1 else 1
    sys_qubits = unitarias[0].num_qubits
    
    qc_select = QuantumCircuit(n + sys_qubits, name="SELECT")
    
    ancillas = list(range(n))
    sistema = list(range(n, n + sys_qubits))
    
    for j in range(k):
        estado_ctrl = format(j, f'0{n}b')
        gate_Uj = unitarias[j].to_gate(label=f"U_{j}")
        ctrl_Uj = gate_Uj.control(num_ctrl_qubits=n, ctrl_state=estado_ctrl)
        qc_select.append(ctrl_Uj, ancillas + sistema)
        
    return qc_select

def build_block_encoding(coeficientes, unitarias):
    """
    Construye el circuito de Block Encoding completo (PREP -> SELECT -> PREP_dagger)
    dada una lista de coeficientes y unitarias.
    """
    prep_circ = build_prep_circuit(coeficientes)
    select_circ = build_select_circuit(unitarias)
    prep_dagger_circ = prep_circ.inverse()
    
    num_ancillas = prep_circ.num_qubits
    sys_qubits = unitarias[0].num_qubits
    
    block_encoding = QuantumCircuit(num_ancillas + sys_qubits, name="Block_Encoding")
    qbts_ancillas = list(range(num_ancillas))
    qbts_total = list(range(num_ancillas + sys_qubits))
    
    block_encoding.append(prep_circ.to_instruction(), qbts_ancillas)
    block_encoding.append(select_circ.to_instruction(), qbts_total)
    block_encoding.append(prep_dagger_circ.to_instruction(), qbts_ancillas)
    
    return block_encoding, num_ancillas