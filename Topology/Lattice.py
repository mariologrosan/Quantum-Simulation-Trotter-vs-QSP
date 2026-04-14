"""
Processor types are named for the general technology qualities that go into builds, consisting of the family and revision. Family (for example, Heron) refers to the size and scale of circuits possible on the chip. This is primarily determined by the number of qubits and the connectivity graph. Revisions (for example, r3) are design variants within a given family, often leading to performance improvements or tradeoffs.
"""

from Header import * 

def DLattice(n_points: int, D: int = 3, dLat: int = 1, origin: bool = False) -> dict:
    """
    Generates an asymmetric lattice embedded in a physical space of dimension 'D'.

    Args:
        n_points (int): The target number of points for the lattice.
        D (int): The physical dimension of the space. Defaults to 3.
        dLat (int): The dimension of the lattice itself. Defaults to 1.
        origin (bool): Flag indicating whether to include the origin point. Defaults to False.

    Returns:
        dict: A dictionary containing:
            - "points" (list of tuples): The spatial coordinates of the generated lattice points.
            - "cod_factor" (float): The coding factor, calculated as the ratio of generated points to requested points.
    """
    if dLat > D:
        raise ValueError(f"Lattice dimension (dLat={dLat}) cannot be larger than physical dimension (D={D})")

    # Calculate the number of points per axis
    if origin:
        points_per_axis = int(np.floor(n_points ** (1 / dLat)))
    else:
        points_per_axis = int(np.floor((n_points + 1) ** (1 / dLat)))

    # Distribute points symmetrically around the origin
    r = points_per_axis // 2 if points_per_axis % 2 == 0 else (points_per_axis - 1) // 2

    axis_ranges = [range(-r, r + 1)] * dLat
    base_points = list(itertools.product(*axis_ranges))

    # Remove the origin if not required
    if not origin:
        zero_vec = (0,) * dLat
        base_points = [p for p in base_points if p != zero_vec]

    # Add padding to reach the physical dimension D
    padding = (0,) * (D - dLat)
    final_points = [p + padding for p in base_points]

    cod_factor = len(final_points) / n_points if n_points > 0 else 0

    return {
        "points": final_points,
        "cod_factor": cod_factor
    }


def get_neighbors(points: list, target_point: tuple) -> list:
    """
    Finds exclusively the orthogonal neighbors of a given 'target_point'.

    Args:
        points (list): A list of tuples representing the available points in the space.
        target_point (tuple): The coordinate tuple for which to find neighbors.

    Returns:
        list: A list of tuples representing the orthogonal neighbors of the target point 
              that exist within the provided 'points' list. Returns an empty list if the 
              target point is not in the set or has no neighbors.
    """
    points_set = set(points)
    if target_point not in points_set:
        return []

    neighbors = []
    dimension = len(target_point)
    
    for i in range(dimension):
        for delta in [-1, 1]:
            neighbor = list(target_point)
            neighbor[i] += delta
            neighbor_tuple = tuple(neighbor)
            if neighbor_tuple in points_set:
                neighbors.append(neighbor_tuple)
                
    return neighbors
    

# =============================================================================
# IBM Quantum Hardware Topologies (in chronological order)
#
# - May 2016: The first publicly accessible backend (5 qubits) was launched (ibmqx1).
# - Early 2017: IBM launched ibmqx2 (IBM Q 5 Yorktown), a 5-qubit backend.
# - June 2017: IBM launched ibmqx3 (IBM Q 16 Rueschlikon), a 16-qubit backend.
# - September 2017: Revised versions of 5-qubit and 16-qubit backends. 
#   ibmqx2 became ibmqx4 (IBM Q 5 Tenerife), and ibmqx3 became ibmqx5 (IBM Q 16 Rueschlikon).
# =============================================================================

def ibmqx1(D: int = 2) -> dict:
    """
    Generates the 5-qubit 'star' topology used in the original 
    IBM Quantum Experience processor from May 2016 (backend name ibmqx1).

    Args:
        D (int): The physical dimension of the space to embed the lattice. Must be >= 2.

    Returns:
        dict: A dictionary containing:
            - "points" (list of tuples): The spatial coordinates of the 5 qubits.
            - "coupling_map" (list): Explicit forward-directed coupling map representing physical connections as [control, target] pairs.
            - "is_directed" (bool): True if the coupling map has a strict directionality (control -> target).
    """
    if D < 2:
        raise ValueError(f"Physical dimension (D={D}) must be at least 2.")

    base_points = [(0, 1), (-1, 0), (0, 0), (1, 0), (0, -1)]
    
    return {
        "points": [p + (0,) * (D - 2) for p in base_points],
        "coupling_map": [[0, 2], [1, 2], [3, 2], [4, 2]],
        "is_directed": True
    }


def ibmqx2(D: int = 2) -> dict:
    """
    Generates the 5-qubit 'bow tie' topology used in IBM Q 5 Yorktown 
    (backend name ibmqx2 and processor type Canary r1).

    Native Gates:
        - Single-qubit: U(θ, φ, λ)
        - Two-qubit: CNOT

    Args:
        D (int): The physical dimension of the space to embed the lattice. Must be >= 2.

    Returns:
        dict: A dictionary containing:
            - "points" (list of tuples): The spatial coordinates of the 5 qubits.
            - "coupling_map" (list): Explicit forward-directed coupling map representing physical connections as [control, target] pairs.
            - "is_directed" (bool): True if the coupling map has a strict directionality (control -> target).
    """
    if D < 2:
        raise ValueError(f"Physical dimension (D={D}) must be at least 2.")

    base_points = [(-1, 1), (-1, -1), (0, 0), (1, 1), (1, -1)]
    
    return {
        "points": [p + (0,) * (D - 2) for p in base_points],
        "coupling_map": [[0, 1], [0, 2], [1, 2], [3, 2], [3, 4], [4, 2]],
        "is_directed": True
    }


def ibmqx3(D: int = 2) -> dict:
    """
    Generates the 16-qubit 2x8 lattice topology used in IBM Q 16 Rueschlikon 
    (backend name ibmqx3 and processor type Canary r1).

    Native Gates:
        - Single-qubit: U(θ, φ, λ)
        - Two-qubit: CNOT

    Args:
        D (int): The physical dimension of the space to embed the lattice. Must be >= 2.

    Returns:
        dict: A dictionary containing:
            - "points" (list of tuples): The spatial coordinates of the 16 qubits.
            - "coupling_map" (list): Explicit forward-directed coupling map representing physical connections as [control, target] pairs.
            - "is_directed" (bool): True if the coupling map has a strict directionality (control -> target).
    """
    if D < 2:
        raise ValueError(f"Physical dimension (D={D}) must be at least 2.")

    base_points = [
        (0, 0), (0, 1), (1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (6, 1),
        (7, 1), (7, 0), (6, 0), (5, 0), (4, 0), (3, 0), (2, 0), (1, 0)
    ]
    
    return {
        "points": [p + (0,) * (D - 2) for p in base_points],
        "coupling_map": [
            [0, 1], [1, 2], [2, 3], [3, 14], [4, 3], [4, 5], 
            [6, 7], [6, 11], [7, 10], [8, 7], [9, 8], [9, 10], 
            [11, 10], [12, 5], [12, 11], [12, 13], [13, 4], [13, 14], 
            [15, 0], [15, 14]
        ],
        "is_directed": True
    }


def ibmqx4(D: int = 2) -> dict:
    """
    Generates the 5-qubit 'bow tie' topology used in IBM Q 5 Tenerife 
    (backend name ibmqx4 and processor type Canary r1).

    Native Gates:
        - Single-qubit: U(θ, φ, λ)
        - Two-qubit: CNOT

    Args:
        D (int): The physical dimension of the space to embed the lattice. Must be >= 2.

    Returns:
        dict: A dictionary containing:
            - "points" (list of tuples): The spatial coordinates of the 5 qubits.
            - "coupling_map" (list): Explicit forward-directed coupling map representing physical connections as [control, target] pairs.
            - "is_directed" (bool): True if the coupling map has a strict directionality (control -> target).
    """
    if D < 2:
        raise ValueError(f"Physical dimension (D={D}) must be at least 2.")

    base_points = [(-1, 1), (-1, -1), (0, 0), (1, 1), (1, -1)]
    
    return {
        "points": [p + (0,) * (D - 2) for p in base_points],
        "coupling_map": [[1, 0], [2, 0], [2, 1], [2, 4], [3, 2], [3, 4]],
        "is_directed": True
    }


def ibmqx5(D: int = 2) -> dict:
    """
    Generates the 16-qubit 2x8 lattice topology used in IBM Q 16 Rueschlikon 
    (backend name ibmqx5 and processor type Canary r1). It is a reconfigured version of ibmqx3.

    Native Gates:
        - Single-qubit: U(θ, φ, λ)
        - Two-qubit: CNOT

    Args:
        D (int): The physical dimension of the space to embed the lattice. Must be >= 2.

    Returns:
        dict: A dictionary containing:
            - "points" (list of tuples): The spatial coordinates of the 16 qubits.
            - "coupling_map" (list): Explicit forward-directed coupling map representing physical connections as [control, target] pairs.
            - "is_directed" (bool): True if the coupling map has a strict directionality (control -> target).
    """
    if D < 2:
        raise ValueError(f"Physical dimension (D={D}) must be at least 2.")

    base_points = [
        (0, 0), (0, 1), (1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (6, 1),
        (7, 1), (7, 0), (6, 0), (5, 0), (4, 0), (3, 0), (2, 0), (1, 0)
    ]
    
    return {
        "points": [p + (0,) * (D - 2) for p in base_points],
        "coupling_map": [
            [1, 0], [1, 2], [2, 3], [3, 4], [3, 14], [5, 4], 
            [6, 5], [6, 7], [6, 11], [7, 10], [8, 7], [9, 8], [9, 10], 
            [11, 10], [12, 5], [12, 11], [12, 13], [13, 4], [13, 14], 
            [15, 0], [15, 2], [15, 14]
        ],
        "is_directed": True
    }

def plot_lattice(lattice_dict, D, show_interactions=True):
    puntos = lattice_dict.get("points", [])
    interacciones = lattice_dict.get("coupling_map", lattice_dict.get("interactions", {}))
    is_directed = lattice_dict.get("is_directed", False) 
    
    if not puntos:
        print("La lattice no tiene puntos para graficar.")
        return

    coordenadas = list(zip(*puntos))
    X = coordenadas[0]
    Y = coordenadas[1] if D >= 2 else [0]*len(X)
    indices = [str(i) for i in range(len(puntos))]
    
    # --- CORRECCIÓN: Normalizar interacciones a una lista de pares ---
    enlaces = []
    if isinstance(interacciones, dict):
        for origen, destinos in interacciones.items():
            for destino in destinos:
                enlaces.append((origen, destino))
    elif isinstance(interacciones, list):
        enlaces = interacciones
    # -----------------------------------------------------------------

    fig = go.Figure()

    if D == 3:
        Z = coordenadas[2]
        if show_interactions and enlaces:
            edge_x, edge_y, edge_z = [], [], []
            for origen, destino in enlaces: # Iteramos sobre la lista normalizada
                p1 = puntos[origen]
                p2 = puntos[destino]
                edge_x.extend([p1[0], p2[0], None])
                edge_y.extend([p1[1], p2[1], None])
                edge_z.extend([p1[2], p2[2], None])
            if edge_x:
                fig.add_trace(go.Scatter3d(
                    x=edge_x, y=edge_y, z=edge_z, mode='lines',
                    line=dict(color='gray', width=3), hoverinfo='none'
                ))

        fig.add_trace(go.Scatter3d(
            x=X, y=Y, z=Z, mode='markers+text', text=indices,
            textposition='top center', textfont=dict(size=12, color='black'),
            marker=dict(size=8, color='blue', opacity=0.8)
        ))
        
        eje_limpio = dict(showticklabels=False, title='', showbackground=False)
        fig.update_layout(
            title="Topología Cuántica 3D", showlegend=False,
            scene=dict(xaxis=eje_limpio, yaxis=eje_limpio, zaxis=eje_limpio, aspectmode='data')
        )
        fig.show()
        
    elif D == 2:
        if show_interactions and enlaces:
            edge_x, edge_y = [], []
            
            for origen, destino in enlaces: # Iteramos sobre la lista normalizada
                p1 = puntos[origen]
                p2 = puntos[destino]
                
                edge_x.extend([p1[0], p2[0], None])
                edge_y.extend([p1[1], p2[1], None])
                
                if is_directed:
                    xm = (p1[0] + p2[0]) / 2  
                    ym = (p1[1] + p2[1]) / 2  
                    
                    fig.add_annotation(
                        ax=p1[0], ay=p1[1],  
                        x=xm, y=ym,          
                        xref="x", yref="y", axref="x", ayref="y",
                        showarrow=True, 
                        arrowhead=2,         
                        arrowsize=1.4,         
                        arrowwidth=1,        
                        arrowcolor="gray",
                        standoff=0           
                    )
            
            if edge_x:
                fig.add_trace(go.Scatter(
                    x=edge_x, y=edge_y, mode='lines',
                    line=dict(color='gray', width=2), hoverinfo='none'
                ))

        fig.add_trace(go.Scatter(
            x=X, y=Y,
            mode='markers+text',
            text=indices,
            textposition='top center',
            textfont=dict(size=14, color='black', family="Arial Black"),
            marker=dict(size=15, color='red')
        ))
        
        fig.update_layout(
            title="Topología Cuántica 2D",
            plot_bgcolor='white', 
            showlegend=False,
            xaxis=dict(showticklabels=False, title='', showgrid=False, zeroline=False),
            yaxis=dict(showticklabels=False, title='', showgrid=False, zeroline=False, scaleanchor="x", scaleratio=1)
        )
        fig.show()