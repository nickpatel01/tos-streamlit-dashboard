import plotly.graph_objects as go

class VolumeChartBuilder:
    def __init__(self, symbol: str):
        self.symbol = symbol

    def create_empty_chart(self) -> go.Figure:
        """Create initial empty chart"""
        fig = go.Figure()
        self._set_layout(fig, 1, None)
        return fig

    def create_chart(self, data: dict, strikes: list, option_symbols: list) -> go.Figure:
        """Build and return the option volume chart"""
        fig = go.Figure()
        
        # Get current price first
        current_price = float(data.get(f"{self.symbol}:LAST", 0))
        if current_price == 0:
            return self.create_empty_chart()
        
        call_volumes, put_volumes = self._calculate_volumes(data, strikes, option_symbols)

        # Convert put volumes to negative for left side display
        neg_put_volumes = [-v for v in put_volumes]

        # Find max values
        max_call = max(call_volumes) if call_volumes else 0
        max_put = max(put_volumes) if put_volumes else 0
        max_abs_value = max(max_call, max_put)
        
        # Ensure we have a non-zero range
        if max_abs_value == 0:
            max_abs_value = 1
            
        # Add padding to the range (20% on each side)
        padding = max_abs_value * 0.2
        chart_range = max_abs_value + padding
        
        self._add_traces(fig, call_volumes, neg_put_volumes, strikes)
        
        # Add horizontal line for current price
        fig.add_hline(
            y=current_price,
            line_color="blue",
            line_width=2,
            line_dash="dash",
            annotation_text=f"${current_price:.2f}",
            annotation_position="top right"
        )
        
        # Add vertical lines at key volume levels
        self._add_volume_markers(fig, chart_range)

        self._set_layout(fig, chart_range, current_price)
        
        return fig

    def _calculate_volumes(self, data, strikes, option_symbols):
        call_volumes = []
        put_volumes = []
        
        for strike in strikes:
            try:
                call_symbol = next(sym for sym in option_symbols if f'C{strike}' in sym)
                put_symbol = next(sym for sym in option_symbols if f'P{strike}' in sym)
                
                # Get volume data
                try:
                    call_vol = float(data.get(f"{call_symbol}:VOLUME", 0))
                except (ValueError, TypeError):
                    call_vol = 0
                    
                try:
                    put_vol = float(data.get(f"{put_symbol}:VOLUME", 0))
                except (ValueError, TypeError):
                    put_vol = 0
                
                call_volumes.append(call_vol)
                put_volumes.append(put_vol)
                
            except StopIteration:
                print(f"Error calculating volume for strike {strike}: {e}")
                call_volumes.append(0)
                put_volumes.append(0)
        
        return call_volumes, put_volumes

    def _add_traces(self, fig, call_volumes, put_volumes, strikes):
        fig.add_trace(go.Bar(
            x=call_volumes,
            y=strikes,
            orientation='h',
            name='Call Volume',
            marker_color='rgba(65, 105, 225, 0.8)',  # Royal blue
            hovertemplate='Strike: %{y}<br>Call Volume: %{x:,}<extra></extra>'
        ))
        
        fig.add_trace(go.Bar(
            x=put_volumes,
            y=strikes,
            orientation='h',
            name='Put Volume',
            marker_color='rgba(255, 182, 193, 0.8)',  # Light pink
            hovertemplate='Strike: %{y}<br>Put Volume: %{x:,}<extra></extra>'
        ))

    def _add_volume_markers(self, fig, chart_range):
        """Add vertical lines at 5K volume intervals"""
        marker_interval = 5000
        num_markers = int(chart_range / marker_interval)
        
        for i in range(1, num_markers + 1):
            vol = i * marker_interval
            # Add markers on both sides
            fig.add_vline(
                x=vol,
                line_color="rgba(0, 255, 0, 0.3)",
                line_width=1,
                line_dash="dot"
            )
            fig.add_vline(
                x=-vol,
                line_color="rgba(0, 255, 0, 0.3)",
                line_width=1,
                line_dash="dot"
            )

    def _set_layout(self, fig, chart_range, current_price=None):
        price_str = f"{current_price:.2f}" if current_price else "--"
        
        fig.update_layout(
            title={
                'text': f'{self.symbol} Option Volume',
                'xanchor': 'center',
                'x': 0.5,
                'font': {'size': 18, 'color': 'white'}
            },
            xaxis_title='Volume',
            yaxis_title='Strike Price',
            barmode='overlay',
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="right",
                x=0.99,
                bgcolor='rgba(0,0,0,0.5)',
                font=dict(color='white')
            ),
            height=600,
            xaxis=dict(
                range=[-chart_range, chart_range],
                zeroline=True,
                zerolinewidth=2,
                zerolinecolor='green',
                tickformat=',',
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
