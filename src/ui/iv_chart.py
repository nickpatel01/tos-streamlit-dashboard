import plotly.graph_objects as go
from plotly.subplots import make_subplots


class IVChartBuilder:
    def __init__(self, symbol: str):
        self.symbol = symbol

    def create_empty_chart(self) -> go.Figure:
        """Create initial empty chart"""
        fig = go.Figure()
        self._set_layout(fig)
        return fig

    def create_chart(self, data: dict, strikes: list, option_symbols: list) -> go.Figure:
        """Build and return the implied volatility chart"""
        fig = make_subplots(specs=[[{"secondary_y": False}]])

        # Get current price
        current_price = float(data.get(f"{self.symbol}:LAST", 0))
        if current_price == 0:
            return self.create_empty_chart()

        call_iv_values, put_iv_values = self._extract_iv_values(data, strikes, option_symbols)

        # Add call IV trace
        fig.add_trace(
            go.Scatter(
                x=strikes,
                y=call_iv_values,
                mode='lines+markers',
                name='Call IV',
                line=dict(color='blue', width=2),
                marker=dict(size=6)
            )
        )

        # Add put IV trace
        fig.add_trace(
            go.Scatter(
                x=strikes,
                y=put_iv_values,
                mode='lines+markers',
                name='Put IV',
                line=dict(color='red', width=2),
                marker=dict(size=6)
            )
        )

        # Add current price line
        fig.add_vline(
            x=current_price,
            line_color="green",
            line_width=2,
            annotation_text=f"${current_price:.2f}",
            annotation_position="top left"
        )

        self._set_layout(fig, current_price)

        return fig

    def _extract_iv_values(self, data, strikes, option_symbols):
        call_iv_values = []
        put_iv_values = []

        for strike in strikes:
            try:
                call_symbol = next(sym for sym in option_symbols if f'C{strike}' in sym)
                put_symbol = next(sym for sym in option_symbols if f'P{strike}' in sym)

                # Get IV values, defaulting to 0 if not available
                try:
                    call_iv = float(data.get(f"{call_symbol}:IMPL_VOL", 0))
                except (ValueError, TypeError):
                    call_iv = 0

                try:
                    put_iv = float(data.get(f"{put_symbol}:IMPL_VOL", 0))
                except (ValueError, TypeError):
                    put_iv = 0

                call_iv_values.append(call_iv)
                put_iv_values.append(put_iv)

            except StopIteration:
                # Strike not found in option_symbols
                call_iv_values.append(None)
                put_iv_values.append(None)
            except Exception:
                call_iv_values.append(None)
                put_iv_values.append(None)

        return call_iv_values, put_iv_values

    def _set_layout(self, fig, current_price=None):
        price_str = f" Price: ${current_price:.2f}" if current_price else ""

        fig.update_layout(
            title={
                'text': f'{self.symbol} Implied Volatility (IV){price_str}',
                'xanchor': 'left',
                'x': 0,
                'font': {'size': 16}
            },
            xaxis_title='Strike Price',
            yaxis_title='Implied Volatility',
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            ),
            height=500,
            hovermode='x unified'
        )
