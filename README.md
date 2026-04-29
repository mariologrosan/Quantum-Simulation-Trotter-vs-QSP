# Benchmarking Quantum Magnetization Dynamics: Trotter-Suzuki vs. QSP/LCU

**Developed during a research internship at the Basque Center for Applied Mathematics (BCAM)**

This repository provides a rigorous, hardware-aware benchmarking framework for simulating the **Transverse Field Ising Model (TFIM)** in the NISQ (Noisy Intermediate-Scale Quantum) era. The primary objective is to analyze the trade-offs between two fundamental quantum time-evolution protocols: the traditional **Trotter-Suzuki decomposition** and the state-of-the-art **Quantum Signal Processing (QSP)** utilizing the **Linear Combination of Unitaries (LCU)** framework.

## Scientific Objective

The core of this research is identifying the empirical **"Crossover Point"**—the threshold where the asymptotic efficiency of QSP overcomes the lower constant overhead of Trotter decomposition. 

While QSP/LCU offers superior scaling for extended time evolution, it requires a significant initial cost (overhead) to construct the **Block Encoding** of the Hamiltonian using ancilla qubits and complex controlled operations. Conversely, Trotter-Suzuki is direct, ancilla-free, and hardware-friendly, but scales poorly in terms of circuit depth as simulation time progresses.

### Key Variable: Topology and SWAP Overhead

A critical differentiator of this study is the impact of hardware connectivity constraints on implementation efficiency:

1.  **Hardware-Adapted Simulation:** Cases where the Hamiltonian connectivity perfectly matches the physical chip topology. Here, Trotter-Suzuki excels by requiring zero routing overhead (SWAP gates).
2.  **Topology-Unaware Simulation:** Scenarios with a topological mismatch force the compiler to insert **SWAP gates**. This study benchmarks how this routing overhead heavily penalizes sequential Trotter algorithms and accelerates the crossover point in favor of QSP, which naturally encapsulates complex, non-local Hamiltonian terms into its block-encoded oracles.

---

## Project Structure

The codebase has been refactored into lean, modular components designed exclusively for research reproducibility and efficiency:

### 📂 `algorithms/`
The core engine of the framework.
*   `qsvt.py`: Implementation of Quantum Signal Processing (QSP) and Quantum Singular Value Transformation (QSVT) phase angles, including exact polynomial degree calculation (via Lambert W function) and the Martini mapping convention.
*   `lcu.py`: Construction of block-encoded oracles (SELECT and PREPARE) for the LCU protocol.
*   `simulation.py`: High-level simulation orchestrator implementing both Trotter-Suzuki (1st Order) and exact QSP/LCU magnetization dynamics pipelines.

### 📂 `dynamics/`
The physics layer of the project.
*   `ising_model.py`: The unified physics module containing the Hamiltonian definitions for the Transverse Field Ising Model (TFIM), providing matrix representations, Pauli-Z measurement operators, computational basis state generation, and the Hamiltonian decomposition required for LCU.

### 📂 `topology/`
The hardware abstraction layer.
*   `lattice.py`: Pre-defined definitions of real quantum hardware topologies (e.g., IBM Quantum's `ibmqx` series) and 3D/2D visualization tools using Plotly to analyze system coupling graphs.

---

## Getting Started

### Prerequisites
*   Python 3.9+

Dependencies are managed via `pyproject.toml` and include `qiskit>=1.0`, `numpy`, `scipy`, `matplotlib`, and `plotly`.

### Installation

Clone the repository and install the framework locally (editable mode is recommended for development):

```bash
git clone <repository_url>
cd Proyecto_BCAM
pip install -e .
```

### Running the Benchmarks
Magnetization simulations can be evaluated directly from Python scripts or Jupyter notebooks. The `algorithms.simulation` module provides the endpoints for comparing expected magnetization $( \langle Z_i \rangle )$ over time for both methods.

```python
import numpy as np
import algorithms.simulation as sim

# 1. Define hardware lattice and physical parameters
lattice_config = {"points": [0, 1, 2], "coupling_map": [(0, 1), (1, 2)]}
hs = [1.0] * 3
Js = {(0, 1): 1.0, (1, 2): 1.0}
ts = np.linspace(0, 1.5, 25)

# 2. Run both simulation methods
mags_qsp = sim.calculate_qsp_magnetization(
    lattice_config, hs, Js, initial_config=[0, 1, 0], time_steps=ts, target_indices=[0, 2]
)
mags_trotter = sim.calculate_trotter_magnetization(
    lattice_config, hs, Js, initial_config=[0, 1, 0], time_steps=ts, target_indices=[0, 2]
)
```

## License
This project is licensed under the MIT License.