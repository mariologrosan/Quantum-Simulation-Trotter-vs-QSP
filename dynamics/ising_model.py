"""
Physics module for the Transverse Field Ising Model (TFIM).

This module provides the Hamiltonian definitions, matrix representations,
Pauli operators, and the Linear Combination of Unitaries (LCU) decomposition
required for quantum simulation.
"""

from typing import List, Dict, Tuple
from functools import reduce
import numpy as np
from qiskit import QuantumCircuit


def get_ising_hamiltonian_matrix(
    lattice: Dict[str, any], 
    external_fields: List[float], 
    coupling_constants: Dict[Tuple[int, int], float]
) -> np.ndarray:
    """Constructs the Hamiltonian matrix for the Transverse Field Ising Model (TFIM).

    The Hamiltonian is constructed using Qiskit's little-endian convention:
    H = Σ h_i Z_i + Σ J_ij X_i X_j

    Args:
        lattice: Dictionary defining the lattice points ('points') and topology ('coupling_map').
        external_fields: List of magnetic field strengths 'h' for each site.
        coupling_constants: Dictionary mapping edge tuples (i, j) to interaction strength 'J'.

    Returns:
        The complete Hamiltonian matrix in the computational basis as a NumPy array.

    Raises:
        ValueError: If the number of fields does not match the number of particles.
    """
    num_particles = len(lattice["points"]) 
    
    if len(external_fields) != num_particles:
        raise ValueError(
            f"Number of fields ({len(external_fields)}) must match particles ({num_particles})."
        )
    
    hilbert_dim = 2 ** num_particles
    hamiltonian = np.zeros((hilbert_dim, hilbert_dim), dtype='float64')
    
    # Local base matrices
    identity = np.eye(2)
    pauli_x = np.array([[0, 1], [1, 0]])
    pauli_z = np.array([[1, 0], [0, -1]])
    
    # 1. External field interaction (Z_i terms)
    for i in range(num_particles):
        operators = [identity] * num_particles        
        operators[i] = pauli_z                    
        
        # Consistent with Qiskit little-endian: reversed kronecker product
        term = external_fields[i] * reduce(np.kron, reversed(operators))
        hamiltonian += term
        
    # 2. Pairwise spin interactions (X_i X_j terms)
    for (i, j), j_value in coupling_constants.items():
        operators = [identity] * num_particles        
        operators[i] = pauli_x                  
        operators[j] = pauli_x                  
        
        term = j_value * reduce(np.kron, reversed(operators))
        hamiltonian += term

    return hamiltonian


def generate_lcu_operators(
    num_qubits: int, 
    external_fields: List[float], 
    coupling_constants: Dict[Tuple[int, int], float]
) -> Tuple[List[float], List[QuantumCircuit]]:
    """Decomposes the Ising Hamiltonian into LCU components (coefficients and unitaries).

    Each term is represented by a positive coefficient and a unitary operator
    (which may include a global phase factor of -1 to handle negative signs).
    H = Σ α_j U_j

    Args:
        num_qubits: Total number of system qubits.
        external_fields: Magnetic field strengths per site.
        coupling_constants: Dictionary of interaction strengths per edge.

    Returns:
        A tuple (coefficients, unitaries) where coefficients is a list of floats
        and unitaries is a list of QuantumCircuit objects.
    """
    lcu_coefficients = []
    lcu_unitaries = []

    # Handle magnetic field terms: g_i * Z_i
    for i in range(num_qubits):
        lcu_coefficients.append(abs(external_fields[i]))
        qc_term = QuantumCircuit(num_qubits)
        
        if external_fields[i] < 0:
            qc_term.global_phase += np.pi
        
        qc_term.z(i)
        lcu_unitaries.append(qc_term)

    # Handle interaction terms: J_ij * X_i * X_j
    for (i, j), j_link in coupling_constants.items():
        lcu_coefficients.append(abs(j_link))
        qc_term = QuantumCircuit(num_qubits)
        
        if j_link < 0:
            qc_term.global_phase += np.pi
            
        qc_term.x(i)
        qc_term.x(j)
        lcu_unitaries.append(qc_term)

    return lcu_coefficients, lcu_unitaries


def get_model_parameters(
    lattice: Dict[str, any], 
    field_strength: float = 1.0, 
    interaction_strength: float = 1.0
) -> Tuple[int, List[float], Dict[Tuple[int, int], float]]:
    """Initializes uniform TFIM parameters for a given lattice topology.

    Args:
        lattice: The target lattice topology dictionary.
        field_strength: Uniform field h for all sites.
        interaction_strength: Uniform interaction J for all edges.

    Returns:
        A tuple (num_qubits, field_list, interaction_dict).
    """
    num_qubits = len(lattice["points"])
    field_list = [field_strength] * num_qubits
    
    interaction_dict = {}
    for (i, j) in lattice.get("coupling_map", []):
        interaction_dict[(i, j)] = interaction_strength
        
    return num_qubits, field_list, interaction_dict


def get_pauli_z_operator(target_index: int, num_particles: int) -> np.ndarray:
    """Builds the operator matrix for a Pauli-Z measurement on a single site.

    Example: for target_index=1 in a 3-qubit system: I ⊗ Z ⊗ I.

    Args:
        target_index: The index of the site to apply Z on (0-indexed).
        num_particles: Total number of particles in the system.

    Returns:
        The operator matrix acting on the full Hilbert space.
    """    
    identity = np.eye(2)
    pauli_z = np.array([[1, 0], [0, -1]])
    
    if target_index == 0:
        total_operator = pauli_z
    else:
        total_operator = identity
        
    for i in range(1, num_particles):
        if i == target_index:
            total_operator = np.kron(total_operator, pauli_z)
        else:
            total_operator = np.kron(total_operator, identity)
            
    return total_operator
    

def generate_computational_basis_state(binary_configuration: List[int]) -> np.ndarray:
    """Generates a normalized state vector from a binary configuration list.

    Args:
        binary_configuration: List of bits (0: Up/|0>, 1: Down/|1>).
            Example: [0, 1, 0] -> |010>.

    Returns:
        The normalized state vector in the Hilbert space.
    """
    state_up = np.array([1, 0], dtype='float64')   # |0>
    state_down = np.array([0, 1], dtype='float64') # |1>
    
    total_state = state_up if binary_configuration[0] == 0 else state_down
    
    for spin in binary_configuration[1:]:
        current_spin_state = state_up if spin == 0 else state_down
        total_state = np.kron(total_state, current_spin_state)
        
    norm = np.linalg.norm(total_state)
    return total_state / norm