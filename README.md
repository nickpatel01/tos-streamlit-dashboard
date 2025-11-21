# TOS Streamlit Dashboard

A real-time multi-page options dashboard using ThinkorSwim's RTD (Real-Time Data) and Streamlit with advanced analytics and export capabilities.

## Demo
https://github.com/user-attachments/assets/1d6446e0-5c49-4208-872f-f63a55da36a5

## Features

### Page 1 - Default Dashboard (`http://localhost:8501`)
- Real-time gamma exposure visualization
- Single-chart focused view
- Quick symbol monitoring

### Page 2 - Advanced Analytics (`http://localhost:8501/page2`)
- **7 Interactive Charts:**
  - Gamma Exposure (GEX) - per 1% move analysis
  - Expected Move - market maker bands
  - Absolute GEX - total exposure view
  - Volume - call/put volume analysis
  - Implied Volatility - IV skew across strikes
  - Greeks - delta, theta, vega, rho visualization
  - Probability - ITM/OTM/Touch probabilities

- **Flexible Strike Range:** 
  - Dual-slider for absolute strike price selection (e.g., 6500-6600)
  - Customizable strike spacing

- **Multi-Format Export:**
  - HTML (interactive charts with zoom/pan)
  - PNG (high-quality static images)
  - JPEG (compressed format)
  - Auto-generated headers with symbol, price, and timestamp
  - Eastern Time timezone support

- **Smart Features:**
  - 2-column responsive chart layout
  - Auto-dismiss notifications (5 seconds)
  - Chart visibility toggles
  - Real-time price display
  - Auto-refresh with configurable intervals

## Prerequisites

- Windows OS (required for ThinkorSwim RTD)
- Python 3.10 to 3.13 (Streamlit not supported in 3.14)
- ThinkorSwim desktop application installed and running

## Installation

1. Clone the repository:
```bash
git clone https://github.com/nickpatel01/tos-streamlit-dashboard
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Start ThinkorSwim desktop application and log in
2. Run the dashboard:
```bash
streamlit run app.py
```
3. Open browser:
   - Default page: `http://localhost:8501`
   - Advanced analytics: `http://localhost:8501/page2`

## Page 2 Controls

### Symbol Configuration
- **Symbol**: Ticker symbol (e.g., "SPX", "SPY")
- **Expiry Date**: Contract expiration date (defaults to nearest Friday)
- **Strike Price Range**: Dual-slider for absolute min/max strike selection
- **Strike Spacing**: Spacing between strikes (e.g., 5, 10, 25)

### Display Options
- **Refresh Rate**: Data update interval (5-60 seconds, default 15)
- **Auto Refresh**: Toggle automatic data updates
- **Chart Toggles**: Show/hide individual charts
- **Export Format**: Select HTML, PNG, or JPEG (PNG default)

### Export Features
- **Filename Format**: `{SYMBOL}-{YYYY-MM-DD_HH-MM-SS}.{ext}` (12-hour Eastern Time)
- **Export Headers**: Includes symbol, current price, and last refresh time
- **Combined Output**: All visible charts in single file
- **Auto-Dismiss**: Success/warning messages clear after 5 seconds

## Technical Details

### Architecture
- **Multi-page Streamlit app** with session state management
- **RTD Integration**: Real-time data via ThinkorSwim COM interface
- **Background Threading**: Non-blocking data updates with graceful shutdown
- **Chart Builders**: Modular design for each visualization type
- **Data Caching**: Centralized cache for efficient chart rendering

### Quote Types Supported
Each option symbol streams 10 real-time fields:
- GAMMA, OPEN_INT (Open Interest), IMPLIED_VOL
- DELTA, THETA, VEGA, RHO
- VOLUME, PROB_ITM, PROB_OTM, PROB_TOUCHING

### Performance
- **Topic Subscriptions**: (strikes × 2 options × 10 fields) + 4 underlying quotes
- Example: 45 strikes = 906 RTD topics
- Optimized for <5 second chart updates with proper error handling

## Notes

- **OnDemand Support**: Works with TOS OnDemand for historical data review on weekends
- **Gamma Display**: Values shown in millions of dollars per 1% move in underlying asset
- **Error 525 Fix**: Simplified chart layouts for reliable PNG/JPEG export
- **Timezone**: All exports use Eastern Time in 12-hour format (no AM/PM)

## Troubleshooting

### Common Issues
1. **Error 525 during export**: Switch to HTML format for most reliable export
2. **No data showing**: Ensure ThinkorSwim is running and logged in
3. **Slow performance**: Reduce strike range or increase refresh interval
4. **Missing chart data**: Some fields (Volume, Probability) may not be available for all option types

## Build

This repo provides a solid foundation - customize it to your needs:
- Add new chart types in `src/ui/`
- Modify RTD fields in `src/rtd/rtd_worker.py`
- Extend export formats in `pages/page2.py`
- Adjust layouts and styling with Streamlit components

Share your builds and we'll maintain a directory of community projects!

## Credit

**Backend:**
[@FollowerOfFlow](https://x.com/FollowerOfFlow) created the TOS RTD Python integration.
Check out [pyrtdc](https://github.com/tifoji/pyrtdc/)

**Gamma Exposure Calculations:**
[perfiliev](https://perfiliev.com/blog/how-to-calculate-gamma-exposure-and-zero-gamma-level/)

**Dashboard Development:**
[@2187Nick](https://x.com/2187Nick)

## Support

[Discord](https://discord.com/invite/vxKepZ6XNC)

<br />
<div align="center">
  <p>Finding value in my work?</p>
  <a href="https://www.buymeacoffee.com/2187Nick" target="_blank"><img src="https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png" alt="Buy Me A Coffee" style="height: 41px !important;width: 174px !important;box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;-webkit-box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;" ></a>
</div>
