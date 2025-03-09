import plotly.graph_objects as go

def create_flight_path_plot(path_coords, area_width, area_height):
    """Create a Plotly figure showing the flight path"""
    x_coords, y_coords = zip(*path_coords)
    
    fig = go.Figure()
    
    # Add flight path
    fig.add_trace(go.Scatter(
        x=x_coords,
        y=y_coords,
        mode='lines+markers',
        name='Flight Path',
        line=dict(color='blue', width=2),
        marker=dict(size=6)
    ))
    
    # Add start point
    fig.add_trace(go.Scatter(
        x=[x_coords[0]],
        y=[y_coords[0]],
        mode='markers',
        name='Start',
        marker=dict(size=12, color='green', symbol='star')
    ))
    
    # Add end point
    fig.add_trace(go.Scatter(
        x=[x_coords[-1]],
        y=[y_coords[-1]],
        mode='markers',
        name='End',
        marker=dict(size=12, color='red', symbol='square')
    ))
    
    # Update layout
    fig.update_layout(
        title="Flight Path Visualization",
        xaxis_title="Distance (meters)",
        yaxis_title="Distance (meters)",
        showlegend=True,
        xaxis=dict(range=[-10, area_width + 10]),
        yaxis=dict(range=[-10, area_height + 10]),
        xaxis_scaleanchor="y",
        xaxis_scaleratio=1,
    )
    
    return fig
