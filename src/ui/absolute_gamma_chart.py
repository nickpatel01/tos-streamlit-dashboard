import plotly.graph_objects as go

class AbsoluteGammaChartBuilder:
    def __init__(self, symbol: str):
        self.symbol = symbol

    def create_empty_chart(self) -> go.Figure:
        """Create initial empty chart"""
        fig = go.Figure()
        self._set_layout(fig, 1, None)
        return fig

    def create_chart(self, data: dict, strikes: list, option_symbols: list) -> go.Figure:
        """Build and return the absolute gamma exposure chart (Call OI + Put OI)"""
        fig = go.Figure()
        
        # Get current price first
        current_price = float(data.get(f"{self.symbol}:LAST", 0))
        if current_price == 0:
            return self.create_empty_chart()
        
        call_oi_values, put_oi_values, total_abs_gex = self._calculate_absolute_gex_values(data, strikes, option_symbols)

        # Find max values and their strikes
        max_call_oi = max(call_oi_values) if call_oi_values else 0
        max_put_oi = max(put_oi_values) if put_oi_values else 0
        max_total = max(total_abs_gex) if total_abs_gex else 0
        
        # Find strike with max total absolute GEX
        max_total_idx = total_abs_gex.index(max_total) if total_abs_gex else -1
        max_total_strike = strikes[max_total_idx] if max_total_idx >= 0 else None
        
        # Find max call and put GEX strikes
        max_call_idx = call_oi_values.index(max_call_oi) if call_oi_values else -1
        max_put_idx = put_oi_values.index(max_put_oi) if put_oi_values else -1
        max_call_strike = strikes[max_call_idx] if max_call_idx >= 0 else None
        max_put_strike = strikes[max_put_idx] if max_put_idx >= 0 else None
        
        # Ensure we have a non-zero range
        max_value = max(max_call_oi, max_put_oi)
        if max_value == 0:
            max_value = 1
            
        # Add padding to the range (20% on each side)
        padding = max_value * 0.2
        chart_range = max_value + padding
        
        self._add_traces(fig, call_oi_values, put_oi_values, strikes)
        
        # Add horizontal line for current price
        fig.add_hline(
            y=current_price,
            line_color="white",
            line_width=2,
            line_dash="dash",
            annotation_text=f"{current_price:.2f}",
            annotation_position="right",
            annotation=dict(
                font=dict(color="white", size=12)
            )
        )

        self._add_annotations(
            fig, max_call_oi, max_put_oi, max_total, padding,
            max_call_strike, max_put_strike, max_total_strike
        )

        self._set_layout(fig, chart_range, current_price, max_total)
        
        return fig

    def _calculate_absolute_gex_values(self, data, strikes, option_symbols):
        call_oi_values = []
        put_oi_values = []
        total_abs_gex = []
        
        try:
            underlying_price = float(data.get(f"{self.symbol}:LAST", 0))
        except (ValueError, TypeError):
            underlying_price = 0
            
        if underlying_price == 0:
            return [], [], []
        
        for strike in strikes:
            try:
                call_symbol = next(sym for sym in option_symbols if f'C{strike}' in sym)
                put_symbol = next(sym for sym in option_symbols if f'P{strike}' in sym)
                
                # Get gamma and OI values
                try:
                    call_gamma = float(data.get(f"{call_symbol}:GAMMA", 0))
                except (ValueError, TypeError):
                    call_gamma = 0
                    
                try:
                    put_gamma = float(data.get(f"{put_symbol}:GAMMA", 0))
                except (ValueError, TypeError):
                    put_gamma = 0
                    
                try:
                    call_oi = float(data.get(f"{call_symbol}:OPEN_INT", 0))
                except (ValueError, TypeError):
                    call_oi = 0
                    
                try:
                    put_oi = float(data.get(f"{put_symbol}:OPEN_INT", 0))
                except (ValueError, TypeError):
                    put_oi = 0
                
                # Calculate absolute gamma exposure per 1% change
                call_gex = abs(call_oi * call_gamma * 100 * (underlying_price * underlying_price) * 0.01)
                put_gex = abs(put_oi * put_gamma * 100 * (underlying_price * underlying_price) * 0.01)
                
                call_oi_values.append(call_gex)
                put_oi_values.append(put_gex)
                total_abs_gex.append(call_gex + put_gex)
                
            except StopIteration:
                print(f"Error calculating absolute GEX for strike {strike}: {e}")
                call_oi_values.append(0)
                put_oi_values.append(0)
                total_abs_gex.append(0)
        
        return call_oi_values, put_oi_values, total_abs_gex

    def _add_traces(self, fig, call_values, put_values, strikes):
        # Add Call OI trace
        fig.add_trace(go.Bar(
            x=call_values,
            y=strikes,
            orientation='h',
            name='Call OI',
            marker_color='rgba(65, 105, 225, 0.9)',  # Royal blue
            hovertemplate='Strike: %{y}<br>Call GEX: $%{x:,.0f}<extra></extra>'
        ))
        
        # Add Put OI trace
        fig.add_trace(go.Bar(
            x=put_values,
            y=strikes,
            orientation='h',
            name='Put OI',
            marker_color='rgba(220, 20, 60, 0.9)',  # Crimson red
            hovertemplate='Strike: %{y}<br>Put GEX: $%{x:,.0f}<extra></extra>'
        ))

    def _add_annotations(self, fig, max_call_oi, max_put_oi, max_total, padding,
                        max_call_strike, max_put_strike, max_total_strike):
        
        # Add annotation for max Call GEX
        if max_call_strike is not None and max_call_oi > 0:
            fig.add_annotation(
                x=max_call_oi,
                y=max_call_strike,
                text=f"Max Call GEX<br>${max_call_oi/1000000:.2f}M<br>{max_call_strike}",
                showarrow=True,
                arrowhead=2,
                arrowcolor="royalblue",
                ax=40,
                ay=-30,
                align="left",
                font=dict(color="royalblue", size=10),
                bgcolor="rgba(0,0,0,0.7)",
                bordercolor="royalblue",
                borderwidth=1
            )
        
        # Add annotation for max Put GEX
        if max_put_strike is not None and max_put_oi > 0:
            fig.add_annotation(
                x=max_put_oi,
                y=max_put_strike,
                text=f"Max Put GEX<br>${max_put_oi/1000000:.2f}M<br>{max_put_strike}",
                showarrow=True,
                arrowhead=2,
                arrowcolor="crimson",
                ax=40,
                ay=30,
                align="left",
                font=dict(color="crimson", size=10),
                bgcolor="rgba(0,0,0,0.7)",
                bordercolor="crimson",
                borderwidth=1
            )
        
        # Add annotation for max total absolute GEX
        if max_total_strike is not None and max_total > 0:
            fig.add_annotation(
                x=max_total * 0.5,  # Position near the middle of the bar
                y=max_total_strike,
                text=f"Max Total abs(GEX)<br>{max_total_strike:.2f}<br>$ per Strike",
                showarrow=True,
                arrowhead=2,
                arrowcolor="yellow",
                ax=-50,
                ay=-40,
                align="center",
                font=dict(color="yellow", size=10),
                bgcolor="rgba(0,0,0,0.8)",
                bordercolor="yellow",
                borderwidth=1
            )

    def _set_layout(self, fig, chart_range, current_price=None, max_total_gex=0):
        price_str = f"{current_price:.2f}" if current_price else "--"
        
        # Calculate total GEX in billions
        total_gex_billions = max_total_gex / 1000000000 if max_total_gex > 0 else 0
        
        fig.update_layout(
            title={
                'text': f'{self.symbol} Total Gamma Exposure<br><sub>Total Gex : ({total_gex_billions:.3f} B)</sub>',
                'xanchor': 'center',
                'x': 0.5,
                'font': {'size': 20, 'color': 'white'}
            },
            xaxis_title='Gamma Exposure',
            yaxis_title='Strike Price',
            barmode='stack',
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
                bgcolor='rgba(0,0,0,0.5)',
                font=dict(color='white', size=12)
            ),
            height=600,
            xaxis=dict(
                range=[0, chart_range],
                zeroline=True,
                zerolinewidth=2,
                zerolinecolor='gray',
                tickformat=',.0f',
                gridcolor='rgba(128, 128, 128, 0.2)',
                color='white'
            ),
            yaxis=dict(
                gridcolor='rgba(128, 128, 128, 0.2)',
                color='white'
            ),
            plot_bgcolor='black',
            paper_bgcolor='black',
            font=dict(color='white')
        )
