"""
Simulation orchestration module for quantum time evolution.

This module provides high-level functions to calculate magnetization dynamics
using Trotter-Suzuki decomposition, Quantum Signal Processing (QSP), and
exact classical matrix exponentiation for benchmarking.
"""

from typing import List, Dict
import numpy as np
import scipy.linalg
from qiskit.quantum_info import Statevector, Pauli
from qiskit import QuantumCircuit

import algorithms.qsvt as qsvt
import algorithms.lcu as lcu
import dynamics.ising_model as ising


def calculate_qsp_magnetization(
    lattice_config: Dict[str, any], 
    fields: List[float], 
    couplings: Dict[tuple, float], 
    initial_config: List[int], 
    time_steps: np.ndarray, 
    target_indices: List[int], 
    error_tolerance: float = 1e-4, 
    scale_factor: float = 0.9
) -> Dict[int, List[float]]:
    """Calculates magnetization evolution using the QSP/QSVT algorithm.

    Args:
        lattice_config: Dictionary defining 'points' and 'coupling_map'.
        fields: List of magnetic field strengths h_i.
        couplings: Dictionary of interaction strengths J_ij.
        initial_config: Binary list representing the initial computational state (0: |0>, 1: |1>).
        time_steps: Array of time points t for the simulation.
        target_indices: System qubit indices to measure <Z> on.
        error_tolerance: Tolerance ε for the Jacobi-Anger expansion.
        scale_factor: Scaling factor to keep the polynomial magnitude within [0, 1].

    Returns:
        A dictionary mapping qubit index to a list of expectation values <Z(t)>.
    """
    num_particles = len(lattice_config["points"])
    coeffs, unitaries = ising.generate_lcu_operators(num_particles, fields, couplings)
    lcu_instruction, num_anc_lcu = lcu.generate_lcu_instruction(coeffs, unitaries)
    norm_alpha = sum(coeffs)
    
    # Total ancilla count: q_b (1) + q_real (1) + phase_anc (1) + num_anc_lcu
    total_ancillas = 3 + num_anc_lcu 
    total_qubits = total_ancillas + num_particles
    
    # Initialize system to the starting configuration
    qc_init = QuantumCircuit(total_qubits)
    for i, bit in enumerate(initial_config):
        if bit == 1:
            qc_init.x(total_ancillas + i)
            
    results = {idx: [] for idx in target_indices}
    

    
    for count, t in enumerate(time_steps):
        if t == 0:
            for idx in target_indices:
                results[idx].append(1.0 if initial_config[idx] == 0 else -1.0)
            continue
            
        # Construct the QSP time evolution circuit
        circ, _ = qsvt.construct_qsvt_time_evolution(
            norm_alpha, t, error_tolerance, scale_factor, lcu_instruction, num_particles, num_anc_lcu
        )
        
        full_circ = qc_init.compose(circ)
        state_vec = Statevector(full_circ)
        
        # Post-select on all ancillas being in the target state for evolution
        # Our implementation targets q_b=|1> and others=|0> for exp(-iHt)
        reshaped = state_vec.data.reshape((2**num_particles, 2**total_ancillas))
        projected_sys = reshaped[:, 1].copy() 
        
        # Normalize the projected statevector (success probability management)
        norm = np.linalg.norm(projected_sys)
        if count == 0:

             
        if norm > 1e-12:
            norm_sys = projected_sys / norm
            sys_sv = Statevector(norm_sys)
            
            # Compute expectation value <Z> for target qubits
            for idx in target_indices:
                pauli_str = ['I'] * num_particles
                pauli_str[idx] = 'Z'
                op = Pauli(''.join(pauli_str[::-1])) 
                val = sys_sv.expectation_value(op).real
                results[idx].append(val)
        else:
            # Handle failure branch (probability leak)
            for idx in target_indices:
                results[idx].append(0.0)
            
    return results


def calculate_exact_magnetization(
    lattice_config: Dict[str, any], 
    fields: List[float], 
    couplings: Dict[tuple, float], 
    initial_config: List[int], 
    time_steps: np.ndarray, 
    target_indices: List[int]
) -> Dict[int, List[float]]:
    """Calculates exact magnetization dynamics using classical matrix exponentiation.

    Args:
        lattice_config: Dictionary containing 'points' and 'coupling_map'.
        fields: Magnetic field strengths.
        couplings: Interaction strengths.
        initial_config: Initial state bitstring.
        time_steps: Array of simulation times.
        target_indices: Qubits to measure.

    Returns:
        Dictionary mapping qubit index to a list of exact expectation values <Z(t)>.
    """
    num_particles = len(lattice_config["points"])
    hamiltonian = ising.get_ising_hamiltonian_matrix(lattice_config, fields, couplings)
    initial_state = ising.generate_computational_basis_state(initial_config)
    
    z_operators = {idx: ising.get_pauli_z_operator(idx, num_particles) for idx in target_indices}
    results = {idx: [] for idx in target_indices}
    

    
    for t in time_steps:
        # |psi(t)> = exp(-iHt) |psi(0)>
        unitary_t = scipy.linalg.expm(-1j * hamiltonian * t)
        state_t = unitary_t @ initial_state
        state_t_conj = np.conjugate(state_t)
        
        for idx in target_indices:
            val = np.dot(state_t_conj, z_operators[idx] @ state_t).real
            results[idx].append(val)
            
    return results


def calculate_trotter_magnetization(
    lattice_config: Dict[str, any], 
    fields: List[float], 
    couplings: Dict[tuple, float], 
    initial_config: List[int], 
    time_steps: np.ndarray, 
    target_indices: List[int], 
    error_tolerance: float = 1e-3
) -> Dict[int, List[float]]:
    """Calculates magnetization evolution using 1st-order Trotter-Suzuki decomposition.

    The number of Trotter steps n is dynamically calculated to respect the
    error tolerance: n ≈ (t * ||H||)^2 / ε.

    Args:
        lattice_config: Hardware topology and coupling map.
        fields: Magnetic field strengths.
        couplings: Interaction strengths.
        initial_config: Initial bitstring.
        time_steps: Simulation times.
        target_indices: Qubits to measure.
        error_tolerance: Target error bound for the decomposition.

    Returns:
        Dictionary mapping qubit index to expectation values <Z(t)>.
    """
    num_particles = len(lattice_config["points"])
    coupling_map = lattice_config["coupling_map"]
    norm_alpha = sum(np.abs(fields)) + sum(np.abs(list(couplings.values())))
    
    results = {idx: [] for idx in target_indices}
    

    
    for t in time_steps:
        if t == 0:
            for idx in target_indices:
                results[idx].append(1.0 if initial_config[idx] == 0 else -1.0)
            continue
            
        num_steps = max(1, int(np.ceil(((t * norm_alpha)**2) / error_tolerance)))
        
        qc = construct_trotter_circuit(lattice_config, fields, couplings, t, error_tolerance, initial_config)
        
        state_vec = Statevector(qc)
        for idx in target_indices:
            pauli_str = ['I'] * num_particles
            pauli_str[idx] = 'Z'
            op = Pauli(''.join(pauli_str[::-1])) 
            val = state_vec.expectation_value(op).real
            results[idx].append(val)
            
    return results


def construct_trotter_circuit(
    lattice_config: Dict[str, any], 
    fields: List[float], 
    couplings: Dict[tuple, float], 
    t: float, 
    error_tolerance: float,
    initial_config: List[int] = None
) -> QuantumCircuit:
    """Constructs the explicit 1st-order Trotter circuit for a single time point.
    
    The number of Trotter steps n is dynamically calculated to respect the
    error tolerance: n ≈ (t * ||H||)^2 / ε.

    Args:
        lattice_config: Topology map.
        fields: Magnetic fields.
        couplings: Interactions.
        t: Target simulation time.
        error_tolerance: Target error bound for the decomposition.
        initial_config: Optional starting bitstring.
        
    Returns:
        A QuantumCircuit representing the Trotterized evolution.
    """
    num_particles = len(lattice_config["points"])
    coupling_map = lattice_config["coupling_map"]
    
    norm_alpha = sum(np.abs(fields)) + sum(np.abs(list(couplings.values())))
    num_steps = max(1, int(np.ceil(((t * norm_alpha)**2) / error_tolerance)))
    dt = t / num_steps
    
    qc = QuantumCircuit(num_particles)
    
    if initial_config is not None:
        for i, bit in enumerate(initial_config):
            if bit == 1:
                qc.x(i)
                
    for _ in range(num_steps):
        for i in range(num_particles):
            qc.rz(2 * fields[i] * dt, i)
        for (i, j) in coupling_map:
            j_val = couplings.get((i, j), couplings.get((j, i), 0.0))
            qc.rxx(2 * j_val * dt, i, j)
            
    return qc
