#  page2.py
import time
import threading
from queue import Queue
from datetime import datetime, date
import streamlit as st
import plotly.io as pio
from src.rtd.rtd_worker import RTDWorker
from src.utils.option_symbol_builder import OptionSymbolBuilder
from src.ui.gamma_chart import GammaChartBuilder
from src.ui.absolute_gamma_chart import AbsoluteGammaChartBuilder
from src.ui.iv_chart import IVChartBuilder
from src.ui.greeks_chart import GreeksChartBuilder
from src.ui.probability_chart import ProbabilityChartBuilder
from src.ui.expected_move_chart import ExpectedMoveChartBuilder
from src.ui.volume_chart import VolumeChartBuilder

# Page configuration
st.set_page_config(page_title="Page 2 - 5 Charts View", layout="wide")

# Initialize session state for page2
if 'p2_initialized' not in st.session_state:
    print("Initializing Page 2")
    st.session_state.p2_initialized = False
    st.session_state.p2_data_queue = Queue()
    st.session_state.p2_stop_event = threading.Event()
    st.session_state.p2_current_price = None
    st.session_state.p2_option_symbols = []
    st.session_state.p2_active_thread = None
    st.session_state.p2_last_gamma_figure = None
    st.session_state.p2_last_abs_gamma_figure = None
    st.session_state.p2_last_iv_figure = None
    st.session_state.p2_last_greeks_figure = None
    st.session_state.p2_last_prob_figure = None
    st.session_state.p2_last_expected_move_figure = None
    st.session_state.p2_last_volume_figure = None
    st.session_state.p2_loading_complete = False
    st.session_state.p2_last_refresh = None
    st.session_state.p2_auto_refresh = True
    # Chart visibility toggles
    st.session_state.p2_show_gex = True
    st.session_state.p2_show_abs_gex = True
    st.session_state.p2_show_iv = True
    st.session_state.p2_show_greeks = True
    st.session_state.p2_show_prob = True
    st.session_state.p2_show_expected = True
    st.session_state.p2_show_volume = True

# Custom CSS
st.markdown("""
<style>
    [data-testid="stStatusWidget"] {visibility: hidden;}
    .stDeployButton {visibility: hidden;}
    div.stButton > button {width: 100%;}
    .chart-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 0;
        margin-bottom: 10px;
    }
    .info-label {
        font-size: 18px;
        font-weight: 600;
        color: #31333f;
        background: #f0f2f6;
        padding: 10px 15px;
        border-radius: 5px;
    }
    .control-section {
        background: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.title("📊 Options Dashboard")

# Header info bar
if 'p2_symbol' in st.session_state and st.session_state.p2_last_refresh:
    st.markdown(f'<div class="info-label">📈 {st.session_state.p2_symbol} | 🕐 Last Refresh: {st.session_state.p2_last_refresh}</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="info-label">📈 Symbol: -- | 🕐 Last Refresh: --</div>', unsafe_allow_html=True)

st.markdown("---")

# Controls Section
with st.container():
    # First row: Symbol, Refresh Rate, Auto Refresh
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
    
    with col1:
        symbol = st.text_input("Symbol", value="SPX", help="Enter stock symbol").upper()
    
    with col2:
        refresh_rate = st.number_input(
            "Refresh Rate (seconds)",
            value=60,
            min_value=5,
            max_value=300,
            step=5,
            help="Chart refresh interval"
        )
    
    with col3:
        auto_refresh = st.checkbox(
            "Auto Refresh", 
            value=st.session_state.p2_auto_refresh,
            key="auto_refresh_toggle",
            help="Automatically refresh charts"
        )
        st.session_state.p2_auto_refresh = auto_refresh
    
    with col4:
        st.markdown('<div style="padding-top: 28px;">', unsafe_allow_html=True)
        start_stop_button = st.button(
            "⏸️ Pause" if st.session_state.p2_initialized else "▶️ Start",
            use_container_width=True,
            type="primary" if not st.session_state.p2_initialized else "secondary"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Second row: Date Selection, Strike Range, Strike Spacing
    col1, col2, col3 = st.columns([2, 3, 2])
    
    with col1:
        expiry_date = st.date_input(
            "Expiration Date",
            value=date.today(),
            format="MM/DD/YYYY",
            help="Select expiration date"
        )
    
    with col2:
        strike_range = st.slider(
            "Strike Range (±)",
            min_value=5,
            max_value=200,
            value=30,
            step=5,
            help="Range of strikes around current price"
        )
    
    with col3:
        strike_spacing = st.selectbox(
            "Strike Spacing",
            options=[0.5, 1.0, 2.5, 5.0, 10.0, 25.0],
            index=3,
            help="Spacing between strikes"
        )

st.markdown("---")

# Chart visibility toggles
st.subheader("Chart Visibility")
col1, col2, col3, col4, col5, col6, col7 = st.columns(7)

with col1:
    st.session_state.p2_show_gex = st.checkbox("GEX", value=st.session_state.p2_show_gex, key="toggle_gex")
with col2:
    st.session_state.p2_show_abs_gex = st.checkbox("Abs GEX", value=st.session_state.p2_show_abs_gex, key="toggle_abs_gex")
with col3:
    st.session_state.p2_show_volume = st.checkbox("Volume", value=st.session_state.p2_show_volume, key="toggle_volume")
with col4:
    st.session_state.p2_show_iv = st.checkbox("IV", value=st.session_state.p2_show_iv, key="toggle_iv")
with col5:
    st.session_state.p2_show_greeks = st.checkbox("Greeks", value=st.session_state.p2_show_greeks, key="toggle_greeks")
with col6:
    st.session_state.p2_show_prob = st.checkbox("Probability", value=st.session_state.p2_show_prob, key="toggle_prob")
with col7:
    st.session_state.p2_show_expected = st.checkbox("Expected Move", value=st.session_state.p2_show_expected, key="toggle_expected")

st.markdown("---")

# Helper function to create download button
def create_download_button(fig, chart_type):
    """Create download button for chart with proper filename"""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{chart_type}_{timestamp}.png"
        img_bytes = pio.to_image(fig, format='png', width=1200, height=600)
        col1, col2 = st.columns([10, 1])
        with col2:
            st.download_button(
                label="📥",
                data=img_bytes,
                file_name=filename,
                mime="image/png",
                key=f"download_{chart_type}_{timestamp}",
                help=f"Download {chart_type} chart"
            )
        return col1
    except Exception as e:
        print(f"Download button error for {chart_type}: {e}")
        return st.container()

# Store symbol for header display
st.session_state.p2_symbol = symbol

# Create placeholders for all charts
chart_placeholders = {
    'gex': None,
    'volume': None,
    'iv': None,
    'greeks': None,
    'prob': None,
    'expected': None
}

# Initialize chart builders if needed
if 'p2_chart_builder' not in st.session_state:
    st.session_state.p2_chart_builder = GammaChartBuilder(symbol)
    st.session_state.p2_abs_gamma_chart_builder = AbsoluteGammaChartBuilder(symbol)
    st.session_state.p2_volume_chart_builder = VolumeChartBuilder(symbol)
    st.session_state.p2_iv_chart_builder = IVChartBuilder(symbol)
    st.session_state.p2_greeks_chart_builder = GreeksChartBuilder(symbol)
    st.session_state.p2_prob_chart_builder = ProbabilityChartBuilder(symbol)
    st.session_state.p2_expected_move_builder = ExpectedMoveChartBuilder(symbol)
    st.session_state.p2_last_gamma_figure = st.session_state.p2_chart_builder.create_empty_chart()

# Display initial empty chart
if st.session_state.p2_last_gamma_figure and st.session_state.p2_show_gex:
    chart_placeholders['gex'] = create_download_button(st.session_state.p2_last_gamma_figure, "GEX")
    chart_placeholders['gex'].plotly_chart(st.session_state.p2_last_gamma_figure, use_container_width=True, key="p2_main_chart")

# Handle start/stop button clicks
if start_stop_button:
    if not st.session_state.p2_initialized:
        # Clean stop any existing thread
        if st.session_state.p2_active_thread:
            st.session_state.p2_stop_event.set()
            st.session_state.p2_active_thread.join(timeout=2.0)
        
        # Reset state
        st.session_state.p2_stop_event = threading.Event()
        st.session_state.p2_data_queue = Queue()
        st.session_state.p2_rtd_worker = RTDWorker(st.session_state.p2_data_queue, st.session_state.p2_stop_event)
        st.session_state.p2_option_symbols = []
        
        # Only reset chart if symbol changed
        if 'p2_last_symbol' not in st.session_state or st.session_state.p2_last_symbol != symbol:
            st.session_state.p2_chart_builder = GammaChartBuilder(symbol)
            st.session_state.p2_abs_gamma_chart_builder = AbsoluteGammaChartBuilder(symbol)
            st.session_state.p2_volume_chart_builder = VolumeChartBuilder(symbol)
            st.session_state.p2_iv_chart_builder = IVChartBuilder(symbol)
            st.session_state.p2_greeks_chart_builder = GreeksChartBuilder(symbol)
            st.session_state.p2_prob_chart_builder = ProbabilityChartBuilder(symbol)
            st.session_state.p2_expected_move_builder = ExpectedMoveChartBuilder(symbol)
            st.session_state.p2_last_gamma_figure = st.session_state.p2_chart_builder.create_empty_chart()
            if st.session_state.p2_show_gex:
                chart_placeholders['gex'] = create_download_button(st.session_state.p2_last_gamma_figure, "GEX")
                chart_placeholders['gex'].plotly_chart(st.session_state.p2_last_gamma_figure, use_container_width=True, key="p2_reset_chart")
            st.session_state.p2_last_symbol = symbol
        
        # Start with stock symbol only to get price first
        try:
            thread = threading.Thread(
                target=st.session_state.p2_rtd_worker.start,
                args=([symbol],),
                daemon=True
            )
            thread.start()
            st.session_state.p2_active_thread = thread
            st.session_state.p2_initialized = True
            time.sleep(0.5)
            st.rerun()
        except Exception as e:
            st.error(f"Failed to start RTD worker: {str(e)}")
            st.session_state.p2_initialized = False
    else:
        # Stop tracking but keep the charts
        st.session_state.p2_stop_event.set()
        if st.session_state.p2_active_thread:
            st.session_state.p2_active_thread.join(timeout=1.0)
        st.session_state.p2_active_thread = None
        st.session_state.p2_initialized = False
        st.session_state.p2_loading_complete = False
        st.session_state.p2_option_symbols = []
        st.rerun()

# Display updates
if st.session_state.p2_initialized and st.session_state.p2_auto_refresh:
    try:
        if not st.session_state.p2_data_queue.empty():
            data = st.session_state.p2_data_queue.get()
            
            if "error" in data:
                st.error(data["error"])
            elif "status" not in data:
                price_key = f"{symbol}:LAST"
                price = data.get(price_key)
                
                if price:
                    # If we just got the price and don't have option symbols yet,
                    # restart with all symbols
                    if not st.session_state.p2_option_symbols:
                        option_symbols = OptionSymbolBuilder.build_symbols(
                            symbol, expiry_date, price, strike_range, strike_spacing
                        )
                        
                        # Stop current thread
                        st.session_state.p2_stop_event.set()
                        if st.session_state.p2_active_thread:
                            st.session_state.p2_active_thread.join(timeout=1.0)
                        
                        # Start new thread with all symbols
                        st.session_state.p2_stop_event = threading.Event()
                        st.session_state.p2_option_symbols = option_symbols
                        all_symbols = [symbol] + option_symbols
                        
                        # Create new RTD worker and thread
                        st.session_state.p2_rtd_worker = RTDWorker(st.session_state.p2_data_queue, st.session_state.p2_stop_event)
                        thread = threading.Thread(
                            target=st.session_state.p2_rtd_worker.start,
                            args=(all_symbols,),
                            daemon=True
                        )
                        thread.start()
                        st.session_state.p2_active_thread = thread
                        time.sleep(0.2)
                
                # Update charts
                if st.session_state.p2_option_symbols:
                    strikes = []
                    for sym in st.session_state.p2_option_symbols:
                        if 'C' in sym:
                            strike_str = sym.split('C')[-1]
                            if '.5' in strike_str:
                                strikes.append(float(strike_str))
                            else:
                                strikes.append(int(strike_str))
                    strikes.sort()

                    # Create all 7 charts
                    gamma_fig = st.session_state.p2_chart_builder.create_chart(data, strikes, st.session_state.p2_option_symbols)
                    abs_gamma_fig = st.session_state.p2_abs_gamma_chart_builder.create_chart(data, strikes, st.session_state.p2_option_symbols)
                    volume_fig = st.session_state.p2_volume_chart_builder.create_chart(data, strikes, st.session_state.p2_option_symbols)
                    iv_fig = st.session_state.p2_iv_chart_builder.create_chart(data, strikes, st.session_state.p2_option_symbols)
                    greeks_fig = st.session_state.p2_greeks_chart_builder.create_chart(data, strikes, st.session_state.p2_option_symbols)
                    prob_fig = st.session_state.p2_prob_chart_builder.create_chart(data, strikes, st.session_state.p2_option_symbols)
                    
                    # Create a copy of gamma chart for expected move visualization
                    expected_move_fig = st.session_state.p2_chart_builder.create_chart(data, strikes, st.session_state.p2_option_symbols)
                    expected_move_fig.update_layout(title="Expected Move with GEX")
                    st.session_state.p2_expected_move_builder.create_reference_lines(expected_move_fig, data)

                    # Update last refresh time
                    st.session_state.p2_last_refresh = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    # Store all figures
                    st.session_state.p2_last_gamma_figure = gamma_fig
                    st.session_state.p2_last_abs_gamma_figure = abs_gamma_fig
                    st.session_state.p2_last_volume_figure = volume_fig
                    st.session_state.p2_last_iv_figure = iv_fig
                    st.session_state.p2_last_greeks_figure = greeks_fig
                    st.session_state.p2_last_prob_figure = prob_fig
                    st.session_state.p2_last_expected_move_figure = expected_move_fig

                    # Display charts based on toggles
                    if st.session_state.p2_show_gex:
                        chart_col = create_download_button(gamma_fig, "GEX")
                        chart_col.plotly_chart(gamma_fig, use_container_width=True, key="p2_update_gamma")
                    
                    if st.session_state.p2_show_abs_gex:
                        chart_col = create_download_button(abs_gamma_fig, "AbsoluteGEX")
                        chart_col.plotly_chart(abs_gamma_fig, use_container_width=True, key="p2_update_abs_gamma")
                    
                    if st.session_state.p2_show_volume:
                        chart_col = create_download_button(volume_fig, "Volume")
                        chart_col.plotly_chart(volume_fig, use_container_width=True, key="p2_update_volume")
                    
                    if st.session_state.p2_show_iv:
                        chart_col = create_download_button(iv_fig, "IV")
                        chart_col.plotly_chart(iv_fig, use_container_width=True, key="p2_update_iv")
                    
                    if st.session_state.p2_show_greeks:
                        chart_col = create_download_button(greeks_fig, "Greeks")
                        chart_col.plotly_chart(greeks_fig, use_container_width=True, key="p2_update_greeks")
                    
                    if st.session_state.p2_show_prob:
                        chart_col = create_download_button(prob_fig, "Probability")
                        chart_col.plotly_chart(prob_fig, use_container_width=True, key="p2_update_prob")
                    
                    if st.session_state.p2_show_expected:
                        chart_col = create_download_button(expected_move_fig, "ExpectedMove")
                        chart_col.plotly_chart(expected_move_fig, use_container_width=True, key="p2_update_expected")

                    if not st.session_state.p2_loading_complete:
                        st.session_state.p2_loading_complete = True
                    else:
                        # Removed blocking time.sleep(refresh_rate / 2)

                    if st.session_state.p2_initialized:
                        st.rerun()
        else:
            if st.session_state.p2_initialized:
                # Removed blocking time.sleep(.5)
                st.rerun()
                
    except Exception as e:
        st.error(f"Display Error: {str(e)}")
        print(f"Error details: {e}")
elif st.session_state.p2_initialized and not st.session_state.p2_auto_refresh:
    # Display static charts when auto-refresh is off
    if st.session_state.p2_last_gamma_figure and st.session_state.p2_show_gex:
        chart_col = create_download_button(st.session_state.p2_last_gamma_figure, "GEX")
        chart_col.plotly_chart(st.session_state.p2_last_gamma_figure, use_container_width=True, key="p2_static_gamma")
    
    if st.session_state.p2_last_abs_gamma_figure and st.session_state.p2_show_abs_gex:
        chart_col = create_download_button(st.session_state.p2_last_abs_gamma_figure, "AbsoluteGEX")
        chart_col.plotly_chart(st.session_state.p2_last_abs_gamma_figure, use_container_width=True, key="p2_static_abs_gamma")
    
    if st.session_state.p2_last_volume_figure and st.session_state.p2_show_volume:
        chart_col = create_download_button(st.session_state.p2_last_volume_figure, "Volume")
        chart_col.plotly_chart(st.session_state.p2_last_volume_figure, use_container_width=True, key="p2_static_volume")
    
    if st.session_state.p2_last_iv_figure and st.session_state.p2_show_iv:
        chart_col = create_download_button(st.session_state.p2_last_iv_figure, "IV")
        chart_col.plotly_chart(st.session_state.p2_last_iv_figure, use_container_width=True, key="p2_static_iv")
    
    if st.session_state.p2_last_greeks_figure and st.session_state.p2_show_greeks:
        chart_col = create_download_button(st.session_state.p2_last_greeks_figure, "Greeks")
        chart_col.plotly_chart(st.session_state.p2_last_greeks_figure, use_container_width=True, key="p2_static_greeks")
    
    if st.session_state.p2_last_prob_figure and st.session_state.p2_show_prob:
        chart_col = create_download_button(st.session_state.p2_last_prob_figure, "Probability")
        chart_col.plotly_chart(st.session_state.p2_last_prob_figure, use_container_width=True, key="p2_static_prob")
    
    if st.session_state.p2_last_expected_move_figure and st.session_state.p2_show_expected:
        chart_col = create_download_button(st.session_state.p2_last_expected_move_figure, "ExpectedMove")
        chart_col.plotly_chart(st.session_state.p2_last_expected_move_figure, use_container_width=True, key="p2_static_expected")
