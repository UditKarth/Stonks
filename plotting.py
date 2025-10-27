"""
Plotting module for interactive payoff diagrams.
"""
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from strategies import Strategy

def plot_payoff_diagram(strategy, price_range=None, current_price=None):
    """
    Create an interactive payoff diagram for a strategy.
    
    Args:
        strategy (Strategy): Strategy object to plot
        price_range (tuple): (min_price, max_price) for the plot range
        current_price (float): Current stock price to mark on the plot
        
    Returns:
        plotly.graph_objects.Figure: Interactive payoff diagram
    """
    # Determine price range if not provided
    if price_range is None:
        strikes = [leg.strike for leg in strategy.legs]
        min_strike = min(strikes)
        max_strike = max(strikes)
        
        # Add some padding around the strikes
        padding = (max_strike - min_strike) * 0.3
        min_price = max(0, min_strike - padding)
        max_price = max_strike + padding
    else:
        min_price, max_price = price_range
    
    # Create price array
    prices = np.linspace(min_price, max_price, 200)
    
    # Calculate payoffs
    payoffs = [strategy.payoff_at_expiration(price) for price in prices]
    
    # Create the main payoff line
    fig = go.Figure()
    
    # Add payoff line
    fig.add_trace(go.Scatter(
        x=prices,
        y=payoffs,
        mode='lines',
        name='Payoff at Expiration',
        line=dict(color='blue', width=3),
        hovertemplate='Stock Price: $%{x:.2f}<br>Payoff: $%{y:.2f}<extra></extra>'
    ))
    
    # Add break-even points
    be_points = strategy.break_even_points()
    be_payoffs = [strategy.payoff_at_expiration(be) for be in be_points]
    
    fig.add_trace(go.Scatter(
        x=be_points,
        y=be_payoffs,
        mode='markers',
        name='Break-Even Points',
        marker=dict(color='red', size=10, symbol='diamond'),
        hovertemplate='Break-Even: $%{x:.2f}<br>Payoff: $%{y:.2f}<extra></extra>'
    ))
    
    # Add current price line if provided
    if current_price is not None:
        current_payoff = strategy.payoff_at_expiration(current_price)
        fig.add_trace(go.Scatter(
            x=[current_price],
            y=[current_payoff],
            mode='markers',
            name='Current Price',
            marker=dict(color='green', size=12, symbol='star'),
            hovertemplate=f'Current Price: ${current_price:.2f}<br>Current Payoff: ${current_payoff:.2f}<extra></extra>'
        ))
        
        # Add vertical line at current price
        fig.add_vline(
            x=current_price,
            line_dash="dash",
            line_color="green",
            annotation_text=f"Current: ${current_price:.2f}",
            annotation_position="top"
        )
    
    # Add zero line
    fig.add_hline(
        y=0,
        line_dash="dot",
        line_color="gray",
        annotation_text="Break-Even Line"
    )
    
    # Update layout
    fig.update_layout(
        title=f'{strategy.name} - Payoff Diagram',
        xaxis_title='Stock Price at Expiration ($)',
        yaxis_title='Profit/Loss ($)',
        hovermode='x unified',
        showlegend=True,
        template='plotly_white',
        height=600,
        margin=dict(l=50, r=50, t=80, b=50)
    )
    
    # Add annotations for key metrics
    max_profit = strategy.max_profit()
    max_loss = strategy.max_loss()
    
    annotations = []
    
    # Add max profit annotation
    if max_profit != float('inf'):
        annotations.append(dict(
            x=0.02,
            y=0.98,
            xref='paper',
            yref='paper',
            text=f'Max Profit: ${max_profit:.2f}',
            showarrow=False,
            bgcolor='lightgreen',
            bordercolor='green',
            borderwidth=1
        ))
    
    # Add max loss annotation
    if max_loss != float('inf'):
        annotations.append(dict(
            x=0.02,
            y=0.90,
            xref='paper',
            yref='paper',
            text=f'Max Loss: ${max_loss:.2f}',
            showarrow=False,
            bgcolor='lightcoral',
            bordercolor='red',
            borderwidth=1
        ))
    
    # Add break-even points annotation
    be_text = f'Break-Even: ${", $".join([f"{be:.2f}" for be in be_points])}'
    annotations.append(dict(
        x=0.02,
        y=0.82,
        xref='paper',
        yref='paper',
        text=be_text,
        showarrow=False,
        bgcolor='lightblue',
        bordercolor='blue',
        borderwidth=1
    ))
    
    fig.update_layout(annotations=annotations)
    
    return fig

def plot_greeks_chart(greeks_data, price_range, current_price=None):
    """
    Create a chart showing how Greeks change with stock price.
    
    Args:
        greeks_data (dict): Dictionary with price arrays and Greek values
        price_range (tuple): (min_price, max_price) for the plot range
        current_price (float): Current stock price to mark on the plot
        
    Returns:
        plotly.graph_objects.Figure: Greeks chart
    """
    fig = go.Figure()
    
    colors = ['blue', 'red', 'green', 'orange', 'purple']
    greek_names = ['Delta', 'Gamma', 'Theta', 'Vega', 'Rho']
    
    for i, (greek_name, values) in enumerate(greeks_data.items()):
        if greek_name.lower() in ['delta', 'gamma', 'theta', 'vega', 'rho']:
            fig.add_trace(go.Scatter(
                x=price_range,
                y=values,
                mode='lines',
                name=greek_name,
                line=dict(color=colors[i % len(colors)], width=2),
                hovertemplate=f'{greek_name}: %{{y:.4f}}<extra></extra>'
            ))
    
    # Add current price line if provided
    if current_price is not None:
        fig.add_vline(
            x=current_price,
            line_dash="dash",
            line_color="gray",
            annotation_text=f"Current: ${current_price:.2f}",
            annotation_position="top"
        )
    
    fig.update_layout(
        title='Greeks vs Stock Price',
        xaxis_title='Stock Price ($)',
        yaxis_title='Greek Value',
        hovermode='x unified',
        showlegend=True,
        template='plotly_white',
        height=500
    )
    
    return fig

def create_strategy_summary_table(strategy, current_price, greeks):
    """
    Create a summary table for the strategy.
    
    Args:
        strategy (Strategy): Strategy object
        current_price (float): Current stock price
        greeks (dict): Greeks values
        
    Returns:
        plotly.graph_objects.Figure: Summary table
    """
    # Calculate current payoff
    current_payoff = strategy.payoff_at_expiration(current_price)
    
    # Create table data
    metrics = [
        ['Strategy', strategy.name],
        ['Current Stock Price', f'${current_price:.2f}'],
        ['Current Payoff', f'${current_payoff:.2f}'],
        ['Max Profit', f'${strategy.max_profit():.2f}' if strategy.max_profit() != float('inf') else 'Unlimited'],
        ['Max Loss', f'${strategy.max_loss():.2f}' if strategy.max_loss() != float('inf') else 'Unlimited'],
        ['Break-Even Points', f'${", $".join([f"{be:.2f}" for be in strategy.break_even_points()])}'],
        ['Net Premium', f'${strategy.total_premium():.2f}'],
        ['Delta', f'{greeks["delta"]:.4f}'],
        ['Gamma', f'{greeks["gamma"]:.4f}'],
        ['Theta', f'{greeks["theta"]:.4f}'],
        ['Vega', f'{greeks["vega"]:.4f}'],
        ['Rho', f'{greeks["rho"]:.4f}']
    ]
    
    fig = go.Figure(data=[go.Table(
        header=dict(
            values=['Metric', 'Value'],
            fill_color='lightblue',
            align='left',
            font=dict(size=14, color='black')
        ),
        cells=dict(
            values=list(zip(*metrics)),
            fill_color='white',
            align='left',
            font=dict(size=12),
            height=30
        )
    )])
    
    fig.update_layout(
        title='Strategy Summary',
        height=400,
        margin=dict(l=20, r=20, t=60, b=20)
    )
    
    return fig
