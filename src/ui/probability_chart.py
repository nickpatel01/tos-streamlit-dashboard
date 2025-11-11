import plotly.graph_objects as go
import numpy as np


class ProbabilityChartBuilder:
    def __init__(self, symbol: str):
        self.symbol = symbol

    def create_empty_chart(self) -> go.Figure:
        """Create initial empty chart"""
        fig = go.Figure()
        self._set_layout(fig)
        return fig

    def create_chart(self, data: dict, strikes: list, option_symbols: list) -> go.Figure:
        """Build and return the probability metrics chart"""
        fig = go.Figure()

        # Get current price
        current_price = float(data.get(f"{self.symbol}:LAST", 0))
        if current_price == 0:
            return self.create_empty_chart()

        # Extract probability values
        prob_expiring, prob_otm, prob_touching = self._extract_probabilities(data, strikes, option_symbols)

        # Add Probability of Expiring ITM trace
        fig.add_trace(
            go.Scatter(
                x=strikes,
                y=prob_expiring,
                mode='lines+markers',
                name='Prob Expiring ITM',
                line=dict(color='green', width=2),
                marker=dict(size=6),
                fill='tozeroy'
            )
        )

        # Add Probability OTM trace
        fig.add_trace(
            go.Scatter(
                x=strikes,
                y=prob_otm,
                mode='lines+markers',
                name='Prob OTM',
                line=dict(color='red', width=2),
                marker=dict(size=6),
                fill='tozeroy'
            )
        )

        # Add Probability of Touching trace
        fig.add_trace(
            go.Scatter(
                x=strikes,
                y=prob_touching,
                mode='lines+markers',
                name='Prob Touching',
                line=dict(color='blue', width=2),
                marker=dict(size=6),
                fill='tozeroy'
            )
        )

        # Add current price line
        fig.add_vline(
            x=current_price,
            line_color="purple",
            line_width=2,
            annotation_text=f"${current_price:.2f}",
            annotation_position="top left"
        )

        # Add 50% probability line
        fig.add_hline(
            y=0.5,
            line_color="gray",
            line_width=1,
            line_dash="dash",
            annotation_text="50%"
        )

        self._set_layout(fig, current_price)

        return fig

    def _extract_probabilities(self, data, strikes, option_symbols):
        prob_expiring = []
        prob_otm = []
        prob_touching = []

        for strike in strikes:
            try:
                call_symbol = next(sym for sym in option_symbols if f'C{strike}' in sym)
                put_symbol = next(sym for sym in option_symbols if f'P{strike}' in sym)

                # Get probability values, defaulting to 0 if not available
                try:
                    call_prob_exp = float(data.get(f"{call_symbol}:PROB_OF_EXPIRING", 0))
                except (ValueError, TypeError):
                    call_prob_exp = 0

                try:
                    call_prob_otm = float(data.get(f"{call_symbol}:PROB_OTM", 0))
                except (ValueError, TypeError):
                    call_prob_otm = 0

                try:
                    call_prob_touch = float(data.get(f"{call_symbol}:PROB_OF_TOUCHING", 0))
                except (ValueError, TypeError):
                    call_prob_touch = 0

                # Use call values for now (could also use put values or average)
                prob_expiring.append(call_prob_exp)
                prob_otm.append(call_prob_otm)
                prob_touching.append(call_prob_touch)

            except StopIteration:
                prob_expiring.append(None)
                prob_otm.append(None)
                prob_touching.append(None)
            except Exception:
                prob_expiring.append(None)
                prob_otm.append(None)
                prob_touching.append(None)

        return prob_expiring, prob_otm, prob_touching

    def _set_layout(self, fig, current_price=None):
        price_str = f" Price: ${current_price:.2f}" if current_price else ""

        fig.update_layout(
            title={
                'text': f'{self.symbol} Probability Metrics{price_str}',
                'xanchor': 'left',
                'x': 0,
                'font': {'size': 16}
            },
            xaxis_title='Strike Price',
            yaxis_title='Probability',
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
