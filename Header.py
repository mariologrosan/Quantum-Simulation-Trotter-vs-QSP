import numpy as np
import itertools
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from scipy.linalg import expm
from functools import reduce
import scipy.constants as const

from qiskit import QuantumCircuit, transpile
from qiskit.circuit.library import StatePreparation
from qiskit.quantum_info import Operator
from qiskit_aer import AerSimulator