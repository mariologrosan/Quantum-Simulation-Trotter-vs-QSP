"""
Hardware topology and lattice definitions module.

This module provides definitions for real quantum processor topologies 
(e.g., IBM Quantum hardware) and utilities to visualize the coupling 
graphs in 2D or 3D.
"""

from typing import List, Dict, Tuple, Optional
import plotly.graph_objects as go


def ibmqx1(space_dim: int = 2) -> Dict[str, any]:
    """Generates the 5-qubit 'star' topology (ibmqx1)."""
    base_points = [(0, 1), (-1, 0), (0, 0), (1, 0), (0, -1)]
    return {
        "points": [p + (0,) * (space_dim - 2) for p in base_points],
        "coupling_map": [[0, 2], [1, 2], [3, 2], [4, 2]],
        "is_directed": True
    }


def ibmqx2(space_dim: int = 2) -> Dict[str, any]:
    """Generates the 5-qubit 'bow tie' topology (ibmqx2 / Yorktown)."""
    base_points = [(-1, 1), (-1, -1), (0, 0), (1, 1), (1, -1)]
    return {
        "points": [p + (0,) * (space_dim - 2) for p in base_points],
        "coupling_map": [[0, 1], [0, 2], [1, 2], [3, 2], [3, 4], [4, 2]],
        "is_directed": True
    }


def ibmqx3(space_dim: int = 2) -> Dict[str, any]:
    """Generates the 16-qubit 2x8 lattice topology (ibmqx3 / Rueschlikon)."""
    base_points = [
        (0, 0), (0, 1), (1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (6, 1),
        (7, 1), (7, 0), (6, 0), (5, 0), (4, 0), (3, 0), (2, 0), (1, 0)
    ]
    return {
        "points": [p + (0,) * (space_dim - 2) for p in base_points],
        "coupling_map": [
            [0, 1], [1, 2], [2, 3], [3, 14], [4, 3], [4, 5], 
            [6, 7], [6, 11], [7, 10], [8, 7], [9, 8], [9, 10], 
            [11, 10], [12, 5], [12, 11], [12, 13], [13, 4], [13, 14], 
            [15, 0], [15, 14]
        ],
        "is_directed": True
    }


def ibmqx4(space_dim: int = 2) -> Dict[str, any]:
    """Generates the 5-qubit 'bow tie' topology (ibmqx4 / Tenerife)."""
    base_points = [(-1, 1), (-1, -1), (0, 0), (1, 1), (1, -1)]
    return {
        "points": [p + (0,) * (space_dim - 2) for p in base_points],
        "coupling_map": [[1, 0], [2, 0], [2, 1], [2, 4], [3, 2], [3, 4]],
        "is_directed": True
    }


def ibmqx5(space_dim: int = 2) -> Dict[str, any]:
    """Generates the 16-qubit 2x8 lattice topology (ibmqx5)."""
    base_points = [
        (0, 0), (0, 1), (1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (6, 1),
        (7, 1), (7, 0), (6, 0), (5, 0), (4, 0), (3, 0), (2, 0), (1, 0)
    ]
    return {
        "points": [p + (0,) * (space_dim - 2) for p in base_points],
        "coupling_map": [
            [1, 0], [1, 2], [2, 3], [3, 4], [3, 14], [5, 4], 
            [6, 5], [6, 7], [6, 11], [7, 10], [8, 7], [9, 8], [9, 10], 
            [11, 10], [12, 5], [12, 11], [12, 13], [13, 4], [13, 14], 
            [15, 0], [15, 2], [15, 14]
        ],
        "is_directed": True
    }


def plot_lattice(
    lattice_dict: Dict[str, any], 
    dimension: int = 2, 
    show_interactions: bool = True
) -> None:
    """Visualizes the quantum hardware topology using Plotly.

    Args:
        lattice_dict: Dictionary containing 'points' (coordinates) and 
            'coupling_map' (list of qubit pairs).
        dimension: Plotting dimension (2 or 3).
        show_interactions: If True, draws lines connecting coupled qubits.
    """
    points = lattice_dict.get("points", [])
    interactions = lattice_dict.get("coupling_map", [])
    is_directed = lattice_dict.get("is_directed", False) 
    
    if not points:
        return

    coordinates = list(zip(*points))
    coord_x = coordinates[0]
    coord_y = coordinates[1] if dimension >= 2 else [0] * len(coord_x)
    indices = [str(i) for i in range(len(points))]
    
    edges = interactions if isinstance(interactions, list) else []

    fig = go.Figure()

    if dimension == 3:
        coord_z = coordinates[2]
        if show_interactions and edges:
            edge_x, edge_y, edge_z = [], [], []
            for origin, dest in edges:
                p1, p2 = points[origin], points[dest]
                edge_x.extend([p1[0], p2[0], None])
                edge_y.extend([p1[1], p2[1], None])
                edge_z.extend([p1[2], p2[2], None])
            if edge_x:
                fig.add_trace(go.Scatter3d(
                    x=edge_x, y=edge_y, z=edge_z, mode='lines',
                    line=dict(color='gray', width=3), hoverinfo='none'
                ))

        fig.add_trace(go.Scatter3d(
            x=coord_x, y=coord_y, z=coord_z, mode='markers+text', text=indices,
            textposition='top center', textfont=dict(size=12, color='black'),
            marker=dict(size=8, color='blue', opacity=0.8)
        ))
        
        clean_axis = dict(showticklabels=False, title='', showbackground=False)
        fig.update_layout(
            title="3D Quantum Hardware Topology", showlegend=False,
            scene=dict(xaxis=clean_axis, yaxis=clean_axis, zaxis=clean_axis, aspectmode='data')
        )
        fig.show()
        
    elif dimension == 2:
        if show_interactions and edges:
            edge_x, edge_y = [], []
            for origin, dest in edges:
                p1, p2 = points[origin], points[dest]
                edge_x.extend([p1[0], p2[0], None])
                edge_y.extend([p1[1], p2[1], None])
                
                if is_directed:
                    x_mid, y_mid = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2  
                    fig.add_annotation(
                        ax=p1[0], ay=p1[1], x=x_mid, y=y_mid,
                        xref="x", yref="y", axref="x", ayref="y",
                        showarrow=True, arrowhead=2, arrowsize=1.4, arrowwidth=1,
                        arrowcolor="gray", standoff=0           
                    )
            
            if edge_x:
                fig.add_trace(go.Scatter(
                    x=edge_x, y=edge_y, mode='lines',
                    line=dict(color='gray', width=2), hoverinfo='none'
                ))

        fig.add_trace(go.Scatter(
            x=coord_x, y=coord_y, mode='markers+text', text=indices,
            textposition='top center',
            textfont=dict(size=14, color='black', family="Arial Black"),
            marker=dict(size=15, color='red')
        ))
        
        fig.update_layout(
            title="2D Quantum Hardware Topology",
            plot_bgcolor='white', showlegend=False,
            xaxis=dict(showticklabels=False, title='', showgrid=False, zeroline=False),
            yaxis=dict(showticklabels=False, title='', showgrid=False, zeroline=False, 
                       scaleanchor="x", scaleratio=1)
        )
        fig.show()