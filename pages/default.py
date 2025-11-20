#  default.py
import time
import threading
from queue import Queue
import streamlit as st
from src.rtd.rtd_worker import RTDWorker
from src.utils.option_symbol_builder import OptionSymbolBuilder
from src.ui.gamma_chart import GammaChartBuilder
from src.ui.iv_chart import IVChartBuilder
from src.ui.greeks_chart import GreeksChartBuilder
from src.ui.probability_chart import ProbabilityChartBuilder
from src.ui.expected_move_chart import ExpectedMoveChartBuilder
from src.ui.dashboard_layout import DashboardLayout

# Initialize session state
if 'initialized' not in st.session_state:
    print("Initializing")
    st.session_state.initialized = False
    st.session_state.data_queue = Queue()
    st.session_state.stop_event = threading.Event()
    st.session_state.current_price = None
    st.session_state.option_symbols = []
    st.session_state.active_thread = None
    st.session_state.last_figure = None
    st.session_state.loading_complete = False
    st.session_state.last_iv_figure = None
    st.session_state.last_greeks_figure = None
    st.session_state.last_prob_figure = None
    st.session_state.last_expected_move_text = None

# Setup UI
DashboardLayout.setup_page()
symbol, expiry_date, strike_range, strike_spacing, refresh_rate, start_stop_button = DashboardLayout.create_input_section()

# Create placeholders for all charts
gamma_chart = st.empty()
iv_chart = st.empty()
greeks_chart = st.empty()
prob_chart = st.empty()
expected_move_display = st.empty()

# Initialize chart builders if needed
if 'chart_builder' not in st.session_state:
    st.session_state.chart_builder = GammaChartBuilder(symbol)
    st.session_state.iv_chart_builder = IVChartBuilder(symbol)
    st.session_state.greeks_chart_builder = GreeksChartBuilder(symbol)
    st.session_state.prob_chart_builder = ProbabilityChartBuilder(symbol)
    st.session_state.expected_move_builder = ExpectedMoveChartBuilder(symbol)
    st.session_state.last_figure = st.session_state.chart_builder.create_empty_chart()

if st.session_state.last_figure:
    gamma_chart.plotly_chart(st.session_state.last_figure, use_container_width=True, key="main_chart")

# Handle start/stop button clicks
if start_stop_button:
    if not st.session_state.initialized:
        # Clean stop any existing thread
        if st.session_state.active_thread:
            st.session_state.stop_event.set()
            st.session_state.active_thread.join(timeout=2.0)  # Increased timeout
        
        # Reset state
        st.session_state.stop_event = threading.Event()
        st.session_state.data_queue = Queue()
        st.session_state.rtd_worker = RTDWorker(st.session_state.data_queue, st.session_state.stop_event)
        st.session_state.option_symbols = []  # Reset option symbols
        
        # Only reset chart if symbol changed
        if 'last_symbol' not in st.session_state or st.session_state.last_symbol != symbol:
            st.session_state.chart_builder = GammaChartBuilder(symbol)
            st.session_state.iv_chart_builder = IVChartBuilder(symbol)
            st.session_state.greeks_chart_builder = GreeksChartBuilder(symbol)
            st.session_state.prob_chart_builder = ProbabilityChartBuilder(symbol)
            st.session_state.expected_move_builder = ExpectedMoveChartBuilder(symbol)
            st.session_state.last_figure = st.session_state.chart_builder.create_empty_chart()
            gamma_chart.plotly_chart(st.session_state.last_figure, use_container_width=True, key="reset_chart")
            st.session_state.last_symbol = symbol
        
        # Start with stock symbol only to get price first
        try:
            thread = threading.Thread(
                target=st.session_state.rtd_worker.start,
                args=([symbol],),
                daemon=True
            )
            thread.start()
            st.session_state.active_thread = thread
            st.session_state.initialized = True
            time.sleep(0.5)  # Give time for initial connection
            st.rerun()
        except Exception as e:
            st.error(f"Failed to start RTD worker: {str(e)}")
            st.session_state.initialized = False
    else:
        # Stop tracking but keep the chart
        st.session_state.stop_event.set()
        if st.session_state.active_thread:
            st.session_state.active_thread.join(timeout=1.0)  # Increased timeout
        st.session_state.active_thread = None
        st.session_state.initialized = False
        st.session_state.loading_complete = False
        st.session_state.option_symbols = []  # Reset option symbols
        #time.sleep(1)  # Add delay before allowing restart
        st.rerun()

# Display updates
if st.session_state.initialized:
    try:
        if not st.session_state.data_queue.empty():
            data = st.session_state.data_queue.get()
            
            if "error" in data:
                st.error(data["error"])
            elif "status" not in data:
                price_key = f"{symbol}:LAST"
                price = data.get(price_key)
                
                if price:
                    # If we just got the price and don't have option symbols yet,
                    # restart with all symbols
                    if not st.session_state.option_symbols:
                        option_symbols = OptionSymbolBuilder.build_symbols(
                            symbol, expiry_date, price, strike_range, strike_spacing
                        )
                        
                        # Stop current thread
                        st.session_state.stop_event.set()
                        if st.session_state.active_thread:
                            st.session_state.active_thread.join(timeout=1.0)
                        
                        # Start new thread with all symbols
                        st.session_state.stop_event = threading.Event()
                        st.session_state.option_symbols = option_symbols
                        all_symbols = [symbol] + option_symbols
                        
                        # Create new RTD worker and thread
                        st.session_state.rtd_worker = RTDWorker(st.session_state.data_queue, st.session_state.stop_event)
                        thread = threading.Thread(
                            target=st.session_state.rtd_worker.start,
                            args=(all_symbols,),
                            daemon=True
                        )
                        thread.start()
                        st.session_state.active_thread = thread
                        time.sleep(0.2)
                
                # Update chart
                if st.session_state.option_symbols:
                    strikes = []
                    for sym in st.session_state.option_symbols:
                        if 'C' in sym:
                            strike_str = sym.split('C')[-1]
                            if '.5' in strike_str:
                                strikes.append(float(strike_str))
                            else:
                                strikes.append(int(strike_str))
                    strikes.sort()

                    # Create all charts
                    gamma_fig = st.session_state.chart_builder.create_chart(data, strikes, st.session_state.option_symbols)
                    iv_fig = st.session_state.iv_chart_builder.create_chart(data, strikes, st.session_state.option_symbols)
                    greeks_fig = st.session_state.greeks_chart_builder.create_chart(data, strikes, st.session_state.option_symbols)
                    prob_fig = st.session_state.prob_chart_builder.create_chart(data, strikes, st.session_state.option_symbols)

                    # Add expected move bands to gamma chart
                    st.session_state.expected_move_builder.create_reference_lines(gamma_fig, data)

                    # Get expected move text
                    expected_move_text = st.session_state.expected_move_builder.get_display_text(data)

                    # Update all displays
                    st.session_state.last_figure = gamma_fig
                    st.session_state.last_iv_figure = iv_fig
                    st.session_state.last_greeks_figure = greeks_fig
                    st.session_state.last_prob_figure = prob_fig
                    st.session_state.last_expected_move_text = expected_move_text

                    gamma_chart.plotly_chart(gamma_fig, use_container_width=True, key="update_gamma")
                    iv_chart.plotly_chart(iv_fig, use_container_width=True, key="update_iv")
                    greeks_chart.plotly_chart(greeks_fig, use_container_width=True, key="update_greeks")
                    prob_chart.plotly_chart(prob_fig, use_container_width=True, key="update_prob")
                    expected_move_display.info(expected_move_text)

                    if not st.session_state.loading_complete:
                        st.session_state.loading_complete = True
                    else:
                        time.sleep(refresh_rate)                     
                    if st.session_state.initialized:
                        st.rerun()
        else:
            if st.session_state.initialized:
                st.sleep(0.5)
                st.rerun()
                
    except Exception as e:
        st.error(f"Display Error: {str(e)}")
        print(f"Error details: {e}")
