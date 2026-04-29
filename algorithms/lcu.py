"""
Module for Linear Combination of Unitaries (LCU) oracles.

This module implements the construction of PREPARE and SELECT oracles
required to build block-encoded unitaries for Hamiltonian simulation.
"""

from typing import List, Tuple
import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit.circuit import Instruction
from qiskit.circuit.library import StatePreparation


def create_preparation_oracle(coefficients: List[float]) -> QuantumCircuit:
    """Creates the PREPARE (PREP) oracle for the LCU method.

    The PREP oracle maps the ground state |0> to a superposition of indices
    weighted by the LCU coefficients: PREP |0> = Σ √(α_j / ||α||) |j>.

    Args:
        coefficients: A list of positive LCU coefficients α_j.

    Returns:
        A QuantumCircuit implementing the state preparation on ancilla qubits.
    """
    total_coeffs = len(coefficients)
    num_ancillas = int(np.ceil(np.log2(total_coeffs))) if total_coeffs > 1 else 1
    sum_abs_coeffs = sum(coefficients)
    
    # Calculate amplitudes for state preparation
    amplitudes = np.zeros(2**num_ancillas, dtype=float)
    for j in range(total_coeffs):
        amplitudes[j] = np.sqrt(coefficients[j] / sum_abs_coeffs)

    prep_gate = StatePreparation(amplitudes)
    qc_prep = QuantumCircuit(num_ancillas, name="PREP")
    qc_prep.append(prep_gate, range(num_ancillas))
    
    return qc_prep


def create_selection_oracle(unitaries: List[QuantumCircuit]) -> QuantumCircuit:
    """Creates the SELECT oracle for the LCU method.

    The SELECT oracle applies unitary U_j to the system register conditioned
    on the ancilla register being in state |j>: SELECT |j>|ψ> = |j> (U_j |ψ>).

    Args:
        unitaries: A list of unitary circuits U_j. All must have the same qubit count.

    Returns:
        A QuantumCircuit combining ancilla and system registers.
    """
    num_unitaries = len(unitaries)
    num_ancillas = int(np.ceil(np.log2(num_unitaries))) if num_unitaries > 1 else 1
    num_system_qubits = unitaries[0].num_qubits
    
    qc_select = QuantumCircuit(num_ancillas + num_system_qubits, name="SELECT")
    
    ancilla_indices = list(range(num_ancillas))
    system_indices = list(range(num_ancillas, num_ancillas + num_system_qubits))
    
    for j in range(num_unitaries):
        unitary_gate = unitaries[j].to_gate(label=f"U_{j}")
        # Apply U_j conditioned on the binary representation of j in ancillas
        controlled_unitary = unitary_gate.control(num_ctrl_qubits=num_ancillas, ctrl_state=j)
        qc_select.append(controlled_unitary, ancilla_indices + system_indices)
        
    return qc_select


def create_block_encoding(
    coefficients: List[float], 
    unitaries: List[QuantumCircuit]
) -> Tuple[QuantumCircuit, int]:
    """Constructs the full Block Encoding circuit (PREP -> SELECT -> PREP†).

    This implements a unitary U such that <0|_a U |0>_a = H / ||α||.

    Args:
        coefficients: The LCU weights α_j.
        unitaries: The list of unitaries U_j in the LCU sum.

    Returns:
        A tuple (block_encoding_circuit, num_ancillas).
    """
    prep_oracle = create_preparation_oracle(coefficients)
    select_oracle = create_selection_oracle(unitaries)
    prep_dagger = prep_oracle.inverse()
    
    num_ancillas = prep_oracle.num_qubits
    num_system_qubits = unitaries[0].num_qubits
    
    block_encoding = QuantumCircuit(num_ancillas + num_system_qubits, name="Block_Encoding")
    ancilla_qubits = list(range(num_ancillas))
    total_qubits = list(range(num_ancillas + num_system_qubits))
    
    block_encoding.append(prep_oracle.to_gate(), ancilla_qubits)
    block_encoding.append(select_oracle.to_gate(), total_qubits)
    block_encoding.append(prep_dagger.to_gate(), ancilla_qubits)
    
    return block_encoding, num_ancillas


def generate_lcu_instruction(
    coefficients: List[float], 
    unitaries: List[QuantumCircuit]
) -> Tuple[Instruction, int]:
    """Generates a high-level Qiskit instruction for the LCU block encoding.

    Args:
        coefficients: The LCU coefficients.
        unitaries: The LCU unitary components.

    Returns:
        A tuple (block_encoding_instruction, num_ancillas).
    """
    raw_circuit, num_ancillas = create_block_encoding(coefficients, unitaries)
    
    # Transpile to gate for easier use in higher-level circuits
    gate = transpile(raw_circuit, optimization_level=0).to_gate()
    gate.name = "Block_Encoding"
    
    return gate, num_ancillas