"""
Quantum Signal Processing (QSP) and Quantum Singular Value Transformation (QSVT) module.

This module implements the calculation of phase angles for Hamiltonian simulation
using the Jacobi-Anger expansion, the determination of optimal polynomial degrees
via the Lambert W function, and the construction of the full QSVT quantum circuits.
"""

from typing import Tuple
import numpy as np
from scipy.special import jv, lambertw
from numpy.polynomial import Chebyshev 
from qiskit import QuantumCircuit, QuantumRegister
from pyqsp.angle_sequence import QuantumSignalProcessingPhases


def compute_cosine_phases(
    hamiltonian_norm: float, 
    time_evolution: float = 0.25, 
    error_tolerance: float = 1e-6, 
    scale_factor: float = 0.9
) -> Tuple[np.ndarray, int]:
    """Computes the QSVT phase angles for the function cos(τ * x).

    Calculates the Jacobi-Anger expansion coefficients and maps them to the
    Martini (Grand Unification) phase convention. The polynomial degree d is
    optimized using the Lambert W function to satisfy the error tolerance.

    Args:
        hamiltonian_norm: The LCU normalization factor (α) of the Hamiltonian.
        time_evolution: The simulation time t.
        error_tolerance: The tolerated approximation error (ε).
        scale_factor: Polynomial scale factor (must be < 1 for QSVT stability).

    Returns:
        A tuple (phases, degree) where phases is a NumPy array of angles
        and degree is the integer polynomial degree d.
    """
    tau = hamiltonian_norm * time_evolution 
    
    # Calculate optimal degree d using Lambert W (arXiv:2512.19665 Eq. 115)
    log_factor = np.log(16 / (5 * error_tolerance))
    w_input = log_factor / (np.e * tau)
    w_val = np.real(lambertw(w_input))
    
    degree = int(2 * np.ceil(log_factor / (2 * w_val)))
    if degree % 2 != 0:
        degree += 1  # Cosine requires even parity
        
    # Jacobi-Anger expansion for cosine: cos(τx) = J_0(τ) + 2 Σ (-1)^k J_{2k}(τ) T_{2k}(x)
    bessel_coeffs = np.zeros(degree + 1)
    bessel_coeffs[0] = jv(0, tau)
    for k in range(1, (degree // 2) + 1):
        bessel_coeffs[2 * k] = 2 * ((-1)**k) * jv(2 * k, tau)
    bessel_coeffs *= scale_factor

    # Convert coefficients to base QSP phases in the Wx convention
    cheb_poly = Chebyshev(bessel_coeffs)
    base_phases = np.array(QuantumSignalProcessingPhases(cheb_poly, signal_operator="Wx"))

    # Map to Martini convention for hardware implementation
    num_angles = degree + 1
    theta = base_phases.copy()
    theta[0] += (3 * np.pi / 4) - ((3 + num_angles % 4) * (np.pi / 2))
    theta[1:-1] += np.pi / 2
    theta[-1] += -np.pi / 4
    
    return theta, degree


def compute_sine_phases(
    hamiltonian_norm: float, 
    time_evolution: float = 0.25, 
    error_tolerance: float = 1e-6, 
    scale_factor: float = 0.9
) -> Tuple[np.ndarray, int]:
    """Computes the QSVT phase angles for the function sin(τ * x).

    Calculates the Jacobi-Anger coefficients for odd parity (sine) and maps
    them to the Martini phase convention.

    Args:
        hamiltonian_norm: The LCU normalization factor (α).
        time_evolution: The simulation time t.
        error_tolerance: The tolerated error (ε).
        scale_factor: Polynomial scale factor.

    Returns:
        A tuple (phases, degree).
    """
    tau = hamiltonian_norm * abs(time_evolution) 
    
    log_factor = np.log(16 / (5 * error_tolerance))
    w_input = log_factor / (np.e * tau)
    w_val = np.real(lambertw(w_input))
    
    degree = int(2 * np.ceil(log_factor / (2 * w_val)))
    if degree % 2 == 0:
        degree += 1  # Sine requires odd parity

    # Jacobi-Anger expansion for sine: sin(τx) = 2 Σ (-1)^k J_{2k+1}(τ) T_{2k+1}(x)
    bessel_coeffs = np.zeros(degree + 1)
    for k in range(0, (degree // 2) + 1):
        bessel_coeffs[2 * k + 1] = 2 * ((-1)**k) * jv(2 * k + 1, tau)
    bessel_coeffs *= scale_factor
    
    if time_evolution < 0:
        bessel_coeffs = -bessel_coeffs

    cheb_poly = Chebyshev(bessel_coeffs)
    base_phases = np.array(QuantumSignalProcessingPhases(cheb_poly, signal_operator="Wx"))

    num_angles = degree + 1
    theta = base_phases.copy()
    theta[0] += (3 * np.pi / 4) - ((3 + num_angles % 4) * (np.pi / 2))
    theta[1:-1] += np.pi / 2
    theta[-1] += -np.pi / 4
    
    return theta, degree


def apply_phase_reflection(
    circuit: QuantumCircuit, 
    ancillas: QuantumRegister, 
    phase_bit: QuantumRegister, 
    phi: float
) -> None:
    """Applies the phase reflection operator: exp(i * φ * (2|0><0| - I)).

    This operator shifts the phase of the all-zero ancilla state. 
    It is implemented as e^{-iφ} * exp(2iφ |0><0|).

    Args:
        circuit: The QuantumCircuit to append the operation to.
        ancillas: The LCU ancilla register.
        phase_bit: The single-qubit phase ancilla register.
        phi: The phase angle φ.
    """
    circuit.global_phase -= phi
    
    # Target all-zero state by wrapping in X gates
    circuit.x(ancillas)
    circuit.x(phase_bit)
    
    # Multi-controlled phase shift
    circuit.mcx(list(ancillas), phase_bit)
    circuit.p(2 * phi, phase_bit)
    circuit.mcx(list(ancillas), phase_bit)
    
    circuit.x(phase_bit)
    circuit.x(ancillas)


def construct_qsvt_circuit(
    phases: np.ndarray, 
    block_encoding_instruction, 
    num_system_qubits: int, 
    num_ancilla_qubits: int,
    adjoint: bool = False
) -> QuantumCircuit:
    """Builds the full QSVT sequence: R(φ_d) U R(φ_{d-1}) ... U R(φ_0).

    Args:
        phases: Array of Martini-mapped phase angles.
        block_encoding_instruction: The instruction (gate) for the Hamiltonian block encoding.
        num_system_qubits: Number of qubits in the physical system.
        num_ancilla_qubits: Number of ancillas in the LCU PREP oracle.
        adjoint: If True, returns the adjoint (inverse) of the QSVT circuit.

    Returns:
        A QuantumCircuit implementing the polynomial transformation.
    """
    degree = len(phases) - 1
    phase_register = QuantumRegister(1, name='phase_anc')
    ancilla_register = QuantumRegister(num_ancilla_qubits, name='anc_lcu')
    system_register = QuantumRegister(num_system_qubits, name='system')
    circuit = QuantumCircuit(phase_register, ancilla_register, system_register)

    if not adjoint:
        for i in range(degree + 1):
            apply_phase_reflection(circuit, ancilla_register, phase_register, phases[i])
            if i < degree:
                circuit.append(block_encoding_instruction, list(ancilla_register) + list(system_register))
    else:
        qc_fwd = construct_qsvt_circuit(
            phases, block_encoding_instruction, num_system_qubits, num_ancilla_qubits, adjoint=False
        )
        circuit.append(qc_fwd.to_gate().inverse(), 
                       list(phase_register) + list(ancilla_register) + list(system_register))
    
    return circuit


def construct_real_part_qsvt(
    phases: np.ndarray, 
    block_encoding_instruction,
    num_system_qubits: int, 
    num_ancilla_qubits: int
) -> QuantumCircuit:
    """Implements the operator (U + U†)/2 via an auxiliary 'real-part' ancilla.

    This uses the Hadamard test structure to select the real part of the 
    polynomial transformation in the block encoding.

    Args:
        phases: Phase angles for the polynomial.
        block_encoding_instruction: The Hamiltonian block encoding gate.
        num_system_qubits: Number of system qubits.
        num_ancilla_qubits: Number of LCU ancillas.

    Returns:
        A QuantumCircuit with an extra 'q_real' ancilla.
    """
    qc_u = construct_qsvt_circuit(phases, block_encoding_instruction, num_system_qubits, num_ancilla_qubits)
    qc_udag = construct_qsvt_circuit(phases, block_encoding_instruction, num_system_qubits, num_ancilla_qubits, adjoint=True)
    
    q_real = QuantumRegister(1, "q_real")
    phase_reg = QuantumRegister(1, "phase_anc")
    anc_lcu = QuantumRegister(num_ancilla_qubits, "anc_lcu")
    sys_reg = QuantumRegister(num_system_qubits, "system")
    
    circuit = QuantumCircuit(q_real, phase_reg, anc_lcu, sys_reg)
    
    circuit.h(q_real)
    # Apply U if q_real is |0>, U† if q_real is |1>
    circuit.append(qc_u.to_gate(label="U").control(1, ctrl_state=0), 
                   [q_real[0]] + list(phase_reg) + list(anc_lcu) + list(sys_reg))
    circuit.append(qc_udag.to_gate(label="U_dag").control(1, ctrl_state=1), 
                   [q_real[0]] + list(phase_reg) + list(anc_lcu) + list(sys_reg))
    circuit.h(q_real)
    
    return circuit


def construct_qsvt_time_evolution(
    hamiltonian_norm: float, 
    time_evolution: float, 
    error_tolerance: float, 
    scale_factor: float,
    block_encoding_instruction, 
    num_system_qubits: int, 
    num_ancilla_qubits: int
) -> Tuple[QuantumCircuit, int]:
    """Constructs the high-level QSP time evolution circuit: exp(-iHt).

    This uses the Linear Combination of Unitaries (LCU) property:
    exp(-iHt) = cos(Ht) - i*sin(Ht). Each part (cos/sin) is constructed as 
    the real part of a QSVT polynomial.

    Args:
        hamiltonian_norm: LCU normalization α.
        time_evolution: Simulation time t.
        error_tolerance: Target error ε.
        scale_factor: Polynomial scaling.
        block_encoding_instruction: Hamiltonian block encoding.
        num_system_qubits: Number of system qubits.
        num_ancilla_qubits: Number of LCU ancillas.

    Returns:
        A tuple (circuit, total_ancilla_count).
    """
    phases_cos, _ = compute_cosine_phases(hamiltonian_norm, time_evolution, error_tolerance, scale_factor)
    phases_sin, _ = compute_sine_phases(hamiltonian_norm, time_evolution, error_tolerance, scale_factor)
    
    qc_re_cos = construct_real_part_qsvt(phases_cos, block_encoding_instruction, num_system_qubits, num_ancilla_qubits)
    qc_re_sin = construct_real_part_qsvt(phases_sin, block_encoding_instruction, num_system_qubits, num_ancilla_qubits)
    
    q_b = QuantumRegister(1, name='q_B')
    q_real = QuantumRegister(1, name="q_real")
    phase_reg = QuantumRegister(1, name='phase_anc')
    anc_lcu = QuantumRegister(num_ancilla_qubits, name='anc_lcu')
    sys_reg = QuantumRegister(num_system_qubits, name='system')
    
    circuit = QuantumCircuit(q_b, q_real, phase_reg, anc_lcu, sys_reg, name="QSP_Time_Evolution")
    
    # Branch selection: Post-selecting q_b on |1> yields (Pc - i*Ps) = exp(-iHt)
    circuit.h(q_b)
    circuit.s(q_b) 
    
    circuit.append(qc_re_cos.to_gate(label="Re_Cos").control(1, ctrl_state=0), 
                   [q_b[0], q_real[0]] + list(phase_reg) + list(anc_lcu) + list(sys_reg))
    circuit.append(qc_re_sin.to_gate(label="Re_Sin").control(1, ctrl_state=1), 
                   [q_b[0], q_real[0]] + list(phase_reg) + list(anc_lcu) + list(sys_reg))
    
    circuit.h(q_b)
    
    total_ancillas = 3 + num_ancilla_qubits 
    return circuit, total_ancillas
