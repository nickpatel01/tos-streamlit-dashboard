#  page2.py
import time
import threading
from queue import Queue
from datetime import datetime, date
from io import BytesIO
import atexit
import streamlit as st
import plotly.io as pio
from PIL import Image
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
st.set_page_config(page_title="Page 2 - Dashboard", layout="wide")

# Cleanup handler for graceful shutdown
def cleanup_on_exit():
    """Clean up RTD connections on exit"""
    if 'p2_stop_event' in st.session_state:
        st.session_state.p2_stop_event.set()
    if 'p2_active_thread' in st.session_state and st.session_state.p2_active_thread:
        try:
            st.session_state.p2_active_thread.join(timeout=2.0)
        except:
            pass
    if 'p2_rtd_worker' in st.session_state and st.session_state.p2_rtd_worker:
        try:
            st.session_state.p2_rtd_worker.cleanup()
        except:
            pass

# Register cleanup handler
atexit.register(cleanup_on_exit)

# Initialize session state for page2
if 'p2_initialized' not in st.session_state:
    print("Initializing Page 2")
    st.session_state.p2_initialized = False
    st.session_state.p2_data_queue = Queue()
    st.session_state.p2_stop_event = threading.Event()
    st.session_state.p2_current_price = None
    st.session_state.p2_option_symbols = []
    st.session_state.p2_active_thread = None
    st.session_state.p2_rtd_worker = None
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
    st.session_state.p2_data_ready = False
    st.session_state.p2_cached_data = None  # Cache the latest RTD data
    # Chart visibility toggles
    st.session_state.p2_show_gex = True
    st.session_state.p2_show_abs_gex = True
    st.session_state.p2_show_iv = True
    st.session_state.p2_show_greeks = True
    st.session_state.p2_show_prob = False  # Disabled by default - no RTD data
    st.session_state.p2_show_expected = True
    st.session_state.p2_show_volume = False  # Disabled by default - no RTD data

# Custom CSS for responsive UI
st.markdown("""
<style>
    [data-testid="stStatusWidget"] {visibility: hidden;}
    .stDeployButton {visibility: hidden;}
    div.stButton > button {
        width: 100%;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        transform: scale(1.02);
    }
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
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .control-section {
        background: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    @media (max-width: 768px) {
        .info-label {
            font-size: 14px;
            padding: 8px 12px;
        }
    }
</style>
""", unsafe_allow_html=True)

# Title and header
col_title, col_download_all = st.columns([5, 1])
with col_title:
    st.title("📊 Options Dashboard")
with col_download_all:
    # Export all visible charts button - generates HTML, PNG, or JPEG
    if st.session_state.p2_data_ready:
        export_format = st.selectbox(
            "Export Format",
            options=["PNG Image", "JPEG Image", "HTML (Interactive)"],
            index=0,  # PNG as default
            key="export_format_select"
        )
        
        if st.button("📥 Export All", key="export_all_btn", help="Download all visible charts in selected format"):
            try:
                from plotly.subplots import make_subplots
                import plotly.graph_objects as go
                from PIL import Image, ImageDraw, ImageFont
                
                # Collect all visible charts
                charts_to_combine = []
                chart_titles = []
                
                if st.session_state.p2_show_gex and st.session_state.p2_last_gamma_figure:
                    charts_to_combine.append(st.session_state.p2_last_gamma_figure)
                    chart_titles.append("Gamma Exposure")
                if st.session_state.p2_show_expected and st.session_state.p2_last_expected_move_figure:
                    charts_to_combine.append(st.session_state.p2_last_expected_move_figure)
                    chart_titles.append("Expected Move")
                if st.session_state.p2_show_abs_gex and st.session_state.p2_last_abs_gamma_figure:
                    charts_to_combine.append(st.session_state.p2_last_abs_gamma_figure)
                    chart_titles.append("Absolute GEX")
                if st.session_state.p2_show_volume and st.session_state.p2_last_volume_figure:
                    charts_to_combine.append(st.session_state.p2_last_volume_figure)
                    chart_titles.append("Volume")
                if st.session_state.p2_show_iv and st.session_state.p2_last_iv_figure:
                    charts_to_combine.append(st.session_state.p2_last_iv_figure)
                    chart_titles.append("Implied Volatility")
                if st.session_state.p2_show_greeks and st.session_state.p2_last_greeks_figure:
                    charts_to_combine.append(st.session_state.p2_last_greeks_figure)
                    chart_titles.append("Greeks")
                if st.session_state.p2_show_prob and st.session_state.p2_last_prob_figure:
                    charts_to_combine.append(st.session_state.p2_last_prob_figure)
                    chart_titles.append("Probability")
                
                if charts_to_combine:
                    # Get Eastern timezone
                    from zoneinfo import ZoneInfo
                    eastern = ZoneInfo("America/New_York")
                    now_eastern = datetime.now(eastern)
                    timestamp = now_eastern.strftime("%Y-%m-%d_%I-%M-%S")  # 12-hour format
                    
                    # Get header info
                    current_price = st.session_state.get('p2_current_price', 0)
                    last_refresh = st.session_state.get('p2_last_refresh_time', datetime.now())
                    
                    # Convert last_refresh to Eastern time if it's not already
                    if last_refresh.tzinfo is None:
                        last_refresh = last_refresh.replace(tzinfo=ZoneInfo("UTC")).astimezone(eastern)
                    refresh_time_str = last_refresh.strftime("%Y-%m-%d %I:%M:%S")  # 12-hour format
                    header_text = f"{st.session_state.p2_symbol} | Price: ${current_price:.2f} | Last Refresh: {refresh_time_str}"
                    
                    if export_format == "HTML (Interactive)":
                        with st.spinner('Generating HTML export...'):
                            # Create subplots with all charts stacked vertically
                            num_charts = len(charts_to_combine)
                            fig_combined = make_subplots(
                                rows=num_charts, 
                                cols=1,
                                subplot_titles=chart_titles,
                                vertical_spacing=0.08,
                                row_heights=[1] * num_charts
                            )
                            
                            # Add each chart to the combined figure
                            for idx, chart in enumerate(charts_to_combine):
                                row_num = idx + 1
                                for trace in chart.data:
                                    fig_combined.add_trace(trace, row=row_num, col=1)
                            
                            # Update layout with header info
                            fig_combined.update_layout(
                                height=600 * num_charts,
                                showlegend=True,
                                title_text=f"{header_text}<br><sub>Options Dashboard - {num_charts} Charts</sub>"
                            )
                            
                            # Generate HTML
                            html_str = fig_combined.to_html(include_plotlyjs='cdn')
                            filename = f"{st.session_state.p2_symbol}-{timestamp}.html"
                            
                            st.download_button(
                                label="⬇️ Download Interactive HTML",
                                data=html_str,
                                file_name=filename,
                                mime="text/html",
                                key="download_combined_html"
                            )
                            # Auto-dismiss success message
                            success_placeholder = st.empty()
                            success_placeholder.success(f"✅ Export ready! ({num_charts} charts combined) - Interactive HTML with zoom and pan")
                            import time
                            time.sleep(5)
                            success_placeholder.empty()
                    
                    else:  # PNG or JPEG export
                        img_format = "png" if export_format == "PNG Image" else "jpeg"
                        mime_type = f"image/{img_format}"
                        
                        with st.spinner(f'Generating {img_format.upper()} export...'):
                            # Convert all charts to images
                            images = []
                            for i, fig in enumerate(charts_to_combine):
                                try:
                                    # Create a simplified copy for export
                                    fig_copy = go.Figure(fig)
                                    
                                    # Simplify layout to avoid Error 525
                                    fig_copy.update_layout(
                                        title=dict(text=chart_titles[i], font=dict(size=16)),
                                        showlegend=True,
                                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                                        annotations=[]  # Remove complex annotations that cause Error 525
                                    )
                                    
                                    img_bytes = pio.to_image(fig_copy, format=img_format, width=1200, height=600)
                                    images.append(Image.open(BytesIO(img_bytes)))
                                except Exception as fig_error:
                                    # Use empty placeholder for auto-dismissing warning
                                    warning_placeholder = st.empty()
                                    warning_placeholder.warning(f"⚠️ Skipped {chart_titles[i]} due to error: {fig_error}")
                                    # Auto-dismiss after 5 seconds
                                    import time
                                    time.sleep(5)
                                    warning_placeholder.empty()
                                    continue
                            
                            if images:
                                # Create header image with info
                                header_height = 80
                                max_width = max(img.width for img in images)
                                header_img = Image.new('RGB', (max_width, header_height), 'white')
                                draw = ImageDraw.Draw(header_img)
                                
                                # Try to use a nice font, fallback to default
                                try:
                                    font = ImageFont.truetype("arial.ttf", 24)
                                    small_font = ImageFont.truetype("arial.ttf", 18)
                                except:
                                    font = ImageFont.load_default()
                                    small_font = ImageFont.load_default()
                                
                                # Draw header text
                                draw.text((20, 15), f"{st.session_state.p2_symbol}", fill='black', font=font)
                                draw.text((20, 45), f"Price: ${current_price:.2f} | Last Refresh: {refresh_time_str}", fill='gray', font=small_font)
                                
                                # Combine header with images vertically
                                total_height = header_height + sum(img.height for img in images)
                                mode = 'RGB'
                                combined_image = Image.new(mode, (max_width, total_height), 'white')
                                
                                # Paste header
                                combined_image.paste(header_img, (0, 0))
                                
                                # Paste charts
                                y_offset = header_height
                                for img in images:
                                    if img.mode != mode:
                                        img = img.convert(mode)
                                    combined_image.paste(img, (0, y_offset))
                                    y_offset += img.height
                                
                                # Convert to bytes
                                buf = BytesIO()
                                if img_format == "jpeg":
                                    combined_image.save(buf, format='JPEG', quality=95)
                                else:
                                    combined_image.save(buf, format='PNG')
                                combined_bytes = buf.getvalue()
                                
                                filename = f"{st.session_state.p2_symbol}-{timestamp}.{img_format}"
                                
                                st.download_button(
                                    label=f"⬇️ Download {img_format.upper()} Image",
                                    data=combined_bytes,
                                    file_name=filename,
                                    mime=mime_type,
                                    key=f"download_combined_{img_format}"
                                )
                                # Auto-dismiss success message
                                success_placeholder = st.empty()
                                success_placeholder.success(f"✅ Export ready! ({len(images)} charts combined)")
                                import time
                                time.sleep(5)
                                success_placeholder.empty()
                            else:
                                st.error("No charts could be converted. Try HTML export instead.")
                else:
                    st.info("No charts selected for export. Enable at least one chart.")
            except Exception as e:
                st.error(f"Export failed: {str(e)}")
                print(f"Export error: {e}")

# Header info bar
if 'p2_symbol' in st.session_state and st.session_state.p2_last_refresh:
    price_display = f'<span style="color: #1E90FF; font-weight: bold; font-size: 18px;">${st.session_state.p2_current_price:.2f}</span>' if st.session_state.p2_current_price else '<span style="color: gray;">--</span>'
    st.markdown(f'<div class="info-label">📈 {st.session_state.p2_symbol} | 💰 Price: {price_display} | 🕐 Last Refresh: {st.session_state.p2_last_refresh}</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="info-label">📈 Symbol: -- | 💰 Price: <span style="color: gray;">--</span> | 🕐 Last Refresh: --</div>', unsafe_allow_html=True)

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
            value=180,
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
        # Get current price for range calculation
        current_price_for_range = st.session_state.p2_current_price if st.session_state.p2_current_price else 6500
        
        # Calculate default range around current price
        default_min = int((current_price_for_range - 100) / 5) * 5
        default_max = int((current_price_for_range + 100) / 5) * 5
        range_min = int((current_price_for_range - 300) / 5) * 5
        range_max = int((current_price_for_range + 300) / 5) * 5
    
    with col3:
        strike_spacing = st.selectbox(
            "Strike Spacing",
            options=[0.5, 1.0, 2.5, 5.0, 10.0, 25.0],
            index=3,
            help="Spacing between strikes"
        )
    
    # Show strike range slider in col2 after spacing is selected
    with col2:
        strike_price_range = st.slider(
            "Strike Price Range",
            min_value=range_min,
            max_value=range_max,
            value=(default_min, default_max),
            step=int(strike_spacing) if strike_spacing >= 1 else 5,
            help="Select min and max strike prices to display"
        )
        strike_range_low = strike_price_range[0]
        strike_range_high = strike_price_range[1]
        
        # Calculate and display number of strikes
        num_strikes = int((strike_range_high - strike_range_low) / strike_spacing) + 1
        # 10 quote types per strike (call+put) × 10 fields + 4 for underlying
        num_topics = num_strikes * 2 * 10 + 4
        st.caption(f"📊 {num_strikes} strikes • {num_topics} RTD topics")

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

# Helper function to create download button with lazy image generation
def create_download_section(chart_type):
    """Create download button section that generates image on-demand"""
    col1, col2 = st.columns([10, 1])
    with col2:
        st.caption("📥")
    return col1

# Actual download handler (only called when button is clicked)
def generate_chart_download(fig, chart_type):
    """Generate downloadable image from chart"""
    try:
        import plotly.graph_objects as go
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{chart_type}_{timestamp}.png"
        
        # Create a copy to avoid state corruption
        fig_copy = go.Figure(fig)
        img_bytes = pio.to_image(fig_copy, format='png', width=1200, height=600)
        
        return img_bytes, filename
    except Exception as e:
        print(f"Download generation error for {chart_type}: {e}")
        return None, None

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

# Display initial empty chart (only when not initialized yet)
if not st.session_state.p2_initialized and st.session_state.p2_last_gamma_figure and st.session_state.p2_show_gex:
    st.plotly_chart(st.session_state.p2_last_gamma_figure, width='stretch', key="p2_initial_chart")

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
                chart_placeholders['gex'] = st.container()
                chart_placeholders['gex'].plotly_chart(st.session_state.p2_last_gamma_figure, width='stretch', key="p2_reset_chart")
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
                        # Store current price for range slider
                        st.session_state.p2_current_price = price
                        
                        option_symbols = OptionSymbolBuilder.build_symbols_from_range(
                            symbol, expiry_date, strike_range_low, strike_range_high, strike_spacing
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
                    try:
                        gamma_fig = st.session_state.p2_chart_builder.create_chart(data, strikes, st.session_state.p2_option_symbols)
                    except Exception as e:
                        print(f"Error creating gamma chart: {e}")
                        gamma_fig = st.session_state.p2_chart_builder.create_empty_chart()
                    
                    try:
                        abs_gamma_fig = st.session_state.p2_abs_gamma_chart_builder.create_chart(data, strikes, st.session_state.p2_option_symbols)
                    except Exception as e:
                        print(f"Error creating absolute gamma chart: {e}")
                        abs_gamma_fig = st.session_state.p2_abs_gamma_chart_builder.create_empty_chart()
                    
                    try:
                        volume_fig = st.session_state.p2_volume_chart_builder.create_chart(data, strikes, st.session_state.p2_option_symbols)
                    except Exception as e:
                        print(f"Error creating volume chart: {e}")
                        volume_fig = st.session_state.p2_volume_chart_builder.create_empty_chart()
                    
                    try:
                        iv_fig = st.session_state.p2_iv_chart_builder.create_chart(data, strikes, st.session_state.p2_option_symbols)
                    except Exception as e:
                        print(f"Error creating IV chart: {e}")
                        iv_fig = st.session_state.p2_iv_chart_builder.create_empty_chart()
                    
                    try:
                        greeks_fig = st.session_state.p2_greeks_chart_builder.create_chart(data, strikes, st.session_state.p2_option_symbols)
                    except Exception as e:
                        print(f"Error creating greeks chart: {e}")
                        greeks_fig = st.session_state.p2_greeks_chart_builder.create_empty_chart()
                    
                    try:
                        prob_fig = st.session_state.p2_prob_chart_builder.create_chart(data, strikes, st.session_state.p2_option_symbols)
                    except Exception as e:
                        print(f"Error creating probability chart: {e}")
                        prob_fig = st.session_state.p2_prob_chart_builder.create_empty_chart()
                    
                    # Create a copy of gamma chart for expected move visualization
                    try:
                        expected_move_fig = st.session_state.p2_chart_builder.create_chart(data, strikes, st.session_state.p2_option_symbols)
                        expected_move_fig.update_layout(title="Expected Move with GEX")
                        st.session_state.p2_expected_move_builder.create_reference_lines(expected_move_fig, data)
                    except Exception as e:
                        print(f"Error creating expected move chart: {e}")
                        expected_move_fig = st.session_state.p2_chart_builder.create_empty_chart()

                    # Update last refresh time
                    st.session_state.p2_last_refresh = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    # Cache the raw data for reuse
                    st.session_state.p2_cached_data = data

                    # Store all figures
                    st.session_state.p2_last_gamma_figure = gamma_fig
                    st.session_state.p2_last_abs_gamma_figure = abs_gamma_fig
                    st.session_state.p2_last_volume_figure = volume_fig
                    st.session_state.p2_last_iv_figure = iv_fig
                    st.session_state.p2_last_greeks_figure = greeks_fig
                    st.session_state.p2_last_prob_figure = prob_fig
                    st.session_state.p2_last_expected_move_figure = expected_move_fig
                    st.session_state.p2_data_ready = True

                    # Display charts based on toggles - 2 per row
                    charts_to_display = []
                    if st.session_state.p2_show_gex and gamma_fig:
                        charts_to_display.append(('gamma', gamma_fig, f"p2_update_gamma_{st.session_state.p2_last_refresh}"))
                    
                    if st.session_state.p2_show_expected and expected_move_fig:
                        charts_to_display.append(('expected', expected_move_fig, f"p2_update_expected_{st.session_state.p2_last_refresh}"))
                    
                    if st.session_state.p2_show_abs_gex and abs_gamma_fig:
                        charts_to_display.append(('abs_gamma', abs_gamma_fig, f"p2_update_abs_gamma_{st.session_state.p2_last_refresh}"))
                    
                    if st.session_state.p2_show_volume and volume_fig:
                        charts_to_display.append(('volume', volume_fig, f"p2_update_volume_{st.session_state.p2_last_refresh}"))
                    
                    if st.session_state.p2_show_iv and iv_fig:
                        charts_to_display.append(('iv', iv_fig, f"p2_update_iv_{st.session_state.p2_last_refresh}"))
                    
                    if st.session_state.p2_show_greeks and greeks_fig:
                        charts_to_display.append(('greeks', greeks_fig, f"p2_update_greeks_{st.session_state.p2_last_refresh}"))
                    
                    if st.session_state.p2_show_prob and prob_fig:
                        charts_to_display.append(('prob', prob_fig, f"p2_update_prob_{st.session_state.p2_last_refresh}"))
                    
                    # Display charts in 2-column layout
                    for i in range(0, len(charts_to_display), 2):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.plotly_chart(charts_to_display[i][1], width='stretch', key=charts_to_display[i][2])
                        if i + 1 < len(charts_to_display):
                            with col2:
                                st.plotly_chart(charts_to_display[i+1][1], width='stretch', key=charts_to_display[i+1][2])

                    if not st.session_state.p2_loading_complete:
                        st.session_state.p2_loading_complete = True
                    else:
                        time.sleep(refresh_rate / 2)

                    if st.session_state.p2_initialized:
                        st.rerun()
        else:
            if st.session_state.p2_initialized:
                time.sleep(.5)
                st.rerun()
                
    except Exception as e:
        st.error(f"Display Error: {str(e)}")
        print(f"Error details: {e}")
elif st.session_state.p2_initialized and not st.session_state.p2_auto_refresh:
    # Display static charts when auto-refresh is off - 2 per row
    static_charts = []
    if st.session_state.p2_last_gamma_figure and st.session_state.p2_show_gex:
        static_charts.append((st.session_state.p2_last_gamma_figure, "p2_static_gamma"))
    
    if st.session_state.p2_last_expected_move_figure and st.session_state.p2_show_expected:
        static_charts.append((st.session_state.p2_last_expected_move_figure, "p2_static_expected"))
    
    if st.session_state.p2_last_abs_gamma_figure and st.session_state.p2_show_abs_gex:
        static_charts.append((st.session_state.p2_last_abs_gamma_figure, "p2_static_abs_gamma"))
    
    if st.session_state.p2_last_volume_figure and st.session_state.p2_show_volume:
        static_charts.append((st.session_state.p2_last_volume_figure, "p2_static_volume"))
    
    if st.session_state.p2_last_iv_figure and st.session_state.p2_show_iv:
        static_charts.append((st.session_state.p2_last_iv_figure, "p2_static_iv"))
    
    if st.session_state.p2_last_greeks_figure and st.session_state.p2_show_greeks:
        static_charts.append((st.session_state.p2_last_greeks_figure, "p2_static_greeks"))
    
    if st.session_state.p2_last_prob_figure and st.session_state.p2_show_prob:
        static_charts.append((st.session_state.p2_last_prob_figure, "p2_static_prob"))
    
    # Display charts in 2-column layout
    for i in range(0, len(static_charts), 2):
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(static_charts[i][0], width='stretch', key=static_charts[i][1])
        if i + 1 < len(static_charts):
            with col2:
                st.plotly_chart(static_charts[i+1][0], width='stretch', key=static_charts[i+1][1])

# Download section at bottom - only shown when data is ready
if st.session_state.p2_data_ready:
    st.markdown("---")
    st.markdown("### 📥 Downloads")
    
    download_cols = st.columns(7)
    chart_mapping = [
        ("GEX", st.session_state.p2_last_gamma_figure, st.session_state.p2_show_gex),
        ("AbsGEX", st.session_state.p2_last_abs_gamma_figure, st.session_state.p2_show_abs_gex),
        ("Volume", st.session_state.p2_last_volume_figure, st.session_state.p2_show_volume),
        ("IV", st.session_state.p2_last_iv_figure, st.session_state.p2_show_iv),
        ("Greeks", st.session_state.p2_last_greeks_figure, st.session_state.p2_show_greeks),
        ("Prob", st.session_state.p2_last_prob_figure, st.session_state.p2_show_prob),
        ("ExpMove", st.session_state.p2_last_expected_move_figure, st.session_state.p2_show_expected),
    ]
    
    for i, (chart_name, fig, is_visible) in enumerate(chart_mapping):
        if is_visible and fig:
            with download_cols[i]:
                if st.button(f"📥 {chart_name}", key=f"dl_{chart_name}", use_container_width=True):
                    img_bytes, filename = generate_chart_download(fig, chart_name)
                    if img_bytes:
                        st.download_button(
                            label=f"⬇️ {chart_name}",
                            data=img_bytes,
                            file_name=filename,
                            mime="image/png",
                            key=f"dl_btn_{chart_name}",
                            use_container_width=True
                        )
                    else:
                        st.error("Error generating image")
