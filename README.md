# BCAM Internship Project: Quantum Simulation (Trotter vs QSP) under Topology Constraints

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Qiskit](https://img.shields.io/badge/qiskit-latest-purple)
![License](https://img.shields.io/badge/license-MIT-green) This repository contains the code developed during my research internship at the **BCAM (Basque Center for Applied Mathematics)** (2026). 

The main objective of this project is to perform a rigorous comparative analysis between the **Trotter-Suzuki** Hamiltonian simulation methods and **Quantum Signal Processing (QSP / LCU)**. Although QSP possesses asymptotic theoretical superiority, it incurs a high initial constant overhead. This project seeks to empirically quantify the exact **crossover point** where QSP becomes more efficient than Trotter in terms of circuit depth and gate count.

To make this study applicable to the NISQ era, the analysis is performed by evaluating the Transverse Field Ising Model (TFIM) under two **hardware topology** scenarios:

1.  **Adapted Hardware (Ideal):** The Hamiltonian matches the chip's physical connectivity, favoring Trotter by avoiding routing overhead.
2.  **Unadapted Hardware (Constrained):** Mismatch between the model and the chip, forcing the compilation of SWAP gates, penalizing the circuit, and evaluating the algorithmic resilience of both methods.

Furthermore, the project implements and faithfully reproduces the quantum hardware benchmarking methodology proposed in the *QuSquare* suite.

---

## 🎯 Specific Study Objectives

* **Algorithm Implementation:** Construction of exact circuits for Trotter evolution and the required *Block Encoding* for QSP.
* **Topology Benchmarking:** Comparison of overhead (CNOT gates, depth) on native topologies versus constrained topologies.
* **Crossover Determination:** Generation of scaling plots to mathematically identify the point at which QSP's "aqueduct" compensates against Trotter's "buckets".

---

## 🧩 Modules and Functions Description

The code is divided into fundamental pillars: Quantum Algorithms, Physical Dynamics, Topology, and Configuration.

### 1. Algorithms/
Contains the pure implementation of quantum algorithms and oracles for QSP.

| File | Main Functions and Description |
| :--- | :--- |
| **`LCU.py`** | `build_prep_circuit(coefficients)`: Creates the PREP oracle that encodes amplitudes $c_j$. <br> `build_select_circuit(unitaries)`: Creates the SELECT oracle to apply $U_j$. <br> `build_block_encoding(...)`: Assembles the final circuit by chaining $\text{PREP} \to \text{SELECT} \to \text{PREP}^\dagger$. |

### 2. Dynamics/
Manages system physics, Hamiltonian construction, and time evolution.

| File | Main Functions and Description |
| :--- | :--- |
| **`Ising.py`** | `H_ising_matrix(...)`: Builds the exact Hamiltonian matrix. <br> `get_lcu_components(...)`: Extracts the coefficients $c_j$ and $U_j$ gates for LCU. |
| **`Dynamics.py`** | `magnetizacion_exacta(...)`: Computes the theoretical evolution of $\langle Z_i \rangle$. <br> `H_ising_circuit(...)`: Builds the time evolution circuit $e^{-iHt}$ via Trotterization. <br> `magnetizacion_qiskit(...)`: Simulates the evolution in `AerSimulator` and extracts transpilation metrics. |
| **`quantum_utils.py`**| `Z_i(...)`: Builds the local operator $\sigma_z$. <br> `generar_estado_base(...)`: Converts a classical configuration into a state vector. |

### 3. Topology/
Core for the study of spatial qubit arrangement and routing.

| File | Main Functions and Description |
| :--- | :--- |
| **`Lattice.py`** | `DLattice(...)`: Computes coordinates of an embedded lattice. <br> `visualize_2D(...)`: Interactive Plotly map to inspect connectivity. |
| **`Interactions.py`**| `interactions(points)`: Determines nearest-neighbor connections. <br> `get_Js(...)`: Maps the topology to coupling constants $J_{ij}$. |

---

## 📂 Project Structure

```text
Proyecto_BCAM/
├── Algorithms/
│   ├── __init__.py
│   └── LCU.py                 
├── Dynamics/
│   ├── __init__.py
│   ├── Dynamics.py            
│   ├── Ising.py               
│   └── quantum_utils.py       
├── Topology/
│   ├── __init__.py
│   ├── Interactions.py        
│   └── Lattice.py             
├── BCAM_intern_project.toml   
├── Header.py                  
└── Pruebas.ipynb
```

## 🛠️ Technologies and Dependencies

This project relies on the Python scientific ecosystem and quantum computing tools:

| Technology | Project Usage |
| :--- | :--- |
| **Qiskit & Qiskit Aer** | Main framework for circuit construction, transpilation, and simulation. |
| **PyQSP** | Numerical calculation of $\phi_k$ phases for signal processing. |
| **NumPy & SciPy** | Heavy linear algebra and exponential matrix validation. |
| **Plotly** | Generation of interactive physical lattice maps. |

---

## 🚀 Usage and Execution

1.  **Environment Setup:** Using a virtual environment managed with **Poetry** is recommended. Install dependencies by running:
    ```bash
    poetry install
    ```
    *(Note: If you prefer `pip`, you can export dependencies from the `.toml` file or install them manually).*

2.  **Workflow:** The main entry point is the `Pruebas.ipynb` notebook. The standard flow consists of:
    * Configuring the geometry in `Lattice.py`.
    * Defining the TFIM parameters in `Ising.py`.
    * Generating the *Block Encoding* with `LCU.py`.
    * Running the simulation and comparing results within the notebook.

---

## 🔬 Methodology (QuSquare)

The development follows the **Ancilla Reflections** architecture proposed in the **QuSquare** benchmarking suite. In contrast to standard QSP implementations, this approach optimizes the use of controlled gates:

* An ancilla register is used for the LCU.
* The signal phase is applied via a reflection operator acting exclusively when the ancilla register is in the $|0\rangle^{\otimes n}$ state.
* This enables the simulation of complex Hamiltonian dynamics with a more efficient circuit depth for Near-Term Intermediate Scale Quantum (NISQ) devices.

---
**Authors:** Mario Logrosán and Rubén Peña
**Contact:** mariologrosan@gmail.com
*Developed within the framework of the BCAM research internship (2026).*