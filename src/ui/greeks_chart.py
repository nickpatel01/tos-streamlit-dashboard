import plotly.graph_objects as go
from plotly.subplots import make_subplots


class GreeksChartBuilder:
    def __init__(self, symbol: str):
        self.symbol = symbol

    def create_empty_chart(self) -> go.Figure:
        """Create initial empty chart"""
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=("Delta", "Gamma", "Theta", "Vega"),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        self._set_layout(fig)
        return fig

    def create_chart(self, data: dict, strikes: list, option_symbols: list) -> go.Figure:
        """Build and return the Greeks chart"""
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=("Delta", "Gamma", "Theta", "Vega"),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )

        # Get current price
        current_price = float(data.get(f"{self.symbol}:LAST", 0))
        if current_price == 0:
            return self.create_empty_chart()

        # Extract Greeks
        deltas, gammas, thetas, vegas = self._extract_greeks(data, strikes, option_symbols)

        # Calculate totals
        total_delta = sum(d for d in deltas if d is not None)
        total_gamma = sum(g for g in gammas if g is not None)
        total_theta = sum(t for t in thetas if t is not None)
        total_vega = sum(v for v in vegas if v is not None)

        # Add Delta subplot
        fig.add_trace(
            go.Scatter(
                x=strikes,
                y=deltas,
                mode='lines+markers',
                name='Delta',
                line=dict(color='blue', width=2),
                marker=dict(size=6),
                fill='tozeroy'
            ),
            row=1, col=1
        )

        # Add Gamma subplot
        fig.add_trace(
            go.Scatter(
                x=strikes,
                y=gammas,
                mode='lines+markers',
                name='Gamma',
                line=dict(color='green', width=2),
                marker=dict(size=6),
                fill='tozeroy'
            ),
            row=1, col=2
        )

        # Add Theta subplot
        fig.add_trace(
            go.Scatter(
                x=strikes,
                y=thetas,
                mode='lines+markers',
                name='Theta',
                line=dict(color='orange', width=2),
                marker=dict(size=6),
                fill='tozeroy'
            ),
            row=2, col=1
        )

        # Add Vega subplot
        fig.add_trace(
            go.Scatter(
                x=strikes,
                y=vegas,
                mode='lines+markers',
                name='Vega',
                line=dict(color='purple', width=2),
                marker=dict(size=6),
                fill='tozeroy'
            ),
            row=2, col=2
        )

        # Add vertical lines for current price on each subplot
        for row in range(1, 3):
            for col in range(1, 3):
                fig.add_vline(
                    x=current_price,
                    line_color="red",
                    line_width=1,
                    line_dash="dash",
                    row=row,
                    col=col
                )

        # Update x-axis labels
        fig.update_xaxes(title_text="Strike", row=1, col=1)
        fig.update_xaxes(title_text="Strike", row=1, col=2)
        fig.update_xaxes(title_text="Strike", row=2, col=1)
        fig.update_xaxes(title_text="Strike", row=2, col=2)

        # Update y-axis labels
        fig.update_yaxes(title_text="Delta", row=1, col=1)
        fig.update_yaxes(title_text="Gamma", row=1, col=2)
        fig.update_yaxes(title_text="Theta", row=2, col=1)
        fig.update_yaxes(title_text="Vega", row=2, col=2)

        self._set_layout(fig, current_price, total_delta, total_gamma, total_theta, total_vega)

        return fig

    def _extract_greeks(self, data, strikes, option_symbols):
        deltas = []
        gammas = []
        thetas = []
        vegas = []

        for strike in strikes:
            try:
                call_symbol = next(sym for sym in option_symbols if f'C{strike}' in sym)
                put_symbol = next(sym for sym in option_symbols if f'P{strike}' in sym)

                # Extract and sum call and put greeks
                try:
                    call_delta = float(data.get(f"{call_symbol}:DELTA", 0))
                    put_delta = float(data.get(f"{put_symbol}:DELTA", 0))
                    delta = call_delta + put_delta
                except (ValueError, TypeError):
                    delta = 0

                try:
                    call_gamma = float(data.get(f"{call_symbol}:GAMMA", 0))
                    put_gamma = float(data.get(f"{put_symbol}:GAMMA", 0))
                    gamma = call_gamma + put_gamma
                except (ValueError, TypeError):
                    gamma = 0

                try:
                    call_theta = float(data.get(f"{call_symbol}:THETA", 0))
                    put_theta = float(data.get(f"{put_symbol}:THETA", 0))
                    theta = call_theta + put_theta
                except (ValueError, TypeError):
                    theta = 0

                try:
                    call_vega = float(data.get(f"{call_symbol}:VEGA", 0))
                    put_vega = float(data.get(f"{put_symbol}:VEGA", 0))
                    vega = call_vega + put_vega
                except (ValueError, TypeError):
                    vega = 0

                deltas.append(delta)
                gammas.append(gamma)
                thetas.append(theta)
                vegas.append(vega)

            except StopIteration:
                deltas.append(None)
                gammas.append(None)
                thetas.append(None)
                vegas.append(None)
            except Exception:
                deltas.append(None)
                gammas.append(None)
                thetas.append(None)
                vegas.append(None)

        return deltas, gammas, thetas, vegas

    def _set_layout(self, fig, current_price=None, total_delta=None, total_gamma=None, total_theta=None, total_vega=None):
        price_str = f" Price: ${current_price:.2f}" if current_price else ""

        # Format totals for display
        totals_str = ""
        if total_delta is not None:
            totals_str += f"ΔTotal: {total_delta:.2f} | "
        if total_gamma is not None:
            totals_str += f"ΓTotal: {total_gamma:.2f} | "
        if total_theta is not None:
            totals_str += f"ΘTotal: {total_theta:.2f} | "
        if total_vega is not None:
            totals_str += f"VTotal: {total_vega:.2f}"

        fig.update_layout(
            title={
                'text': f'{self.symbol} Greeks Analysis{price_str}<br><sub>{totals_str}</sub>',
                'xanchor': 'left',
                'x': 0,
                'font': {'size': 14}
            },
            height=700,
            showlegend=False,
            hovermode='x unified'
        )
