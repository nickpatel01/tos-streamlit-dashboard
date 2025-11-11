import plotly.graph_objects as go


class ExpectedMoveChartBuilder:
    def __init__(self, symbol: str):
        self.symbol = symbol

    def create_empty_display(self) -> dict:
        """Create empty display metrics"""
        return {
            "market_maker_move": None,
            "front_ex_move": None,
            "back_ex_move": None,
            "upper_band": None,
            "lower_band": None,
            "current_price": None
        }

    def extract_metrics(self, data: dict) -> dict:
        """Extract expected move metrics from data"""
        current_price = float(data.get(f"{self.symbol}:LAST", 0))

        if current_price == 0:
            return self.create_empty_display()

        # Try to get move values from data
        try:
            market_maker_move = float(data.get(f"{self.symbol}:MRKT_MKR_MOVE", 0))
        except (ValueError, TypeError):
            market_maker_move = 0

        try:
            front_ex_move = float(data.get(f"{self.symbol}:FRONT_EX_MOVE", 0))
        except (ValueError, TypeError):
            front_ex_move = 0

        try:
            back_ex_move = float(data.get(f"{self.symbol}:BACK_EX_MOVE", 0))
        except (ValueError, TypeError):
            back_ex_move = 0

        # Calculate bands using market maker move
        if market_maker_move > 0:
            upper_band = current_price + market_maker_move
            lower_band = current_price - market_maker_move
        else:
            upper_band = None
            lower_band = None

        return {
            "market_maker_move": market_maker_move,
            "front_ex_move": front_ex_move,
            "back_ex_move": back_ex_move,
            "upper_band": upper_band,
            "lower_band": lower_band,
            "current_price": current_price
        }

    def create_reference_lines(self, fig, data: dict):
        """Add expected move reference lines to an existing figure (for Gamma chart)"""
        metrics = self.extract_metrics(data)

        if metrics["current_price"] is None or metrics["current_price"] == 0:
            return

        # Add market maker expected move bands
        if metrics["upper_band"] is not None:
            fig.add_hline(
                y=metrics["upper_band"],
                line_color="orange",
                line_width=1,
                line_dash="dash",
                annotation_text=f"Upper Band: ${metrics['upper_band']:.2f}",
                annotation_position="right"
            )

        if metrics["lower_band"] is not None:
            fig.add_hline(
                y=metrics["lower_band"],
                line_color="orange",
                line_width=1,
                line_dash="dash",
                annotation_text=f"Lower Band: ${metrics['lower_band']:.2f}",
                annotation_position="right"
            )

    def get_display_text(self, data: dict) -> str:
        """Get formatted text for metrics display"""
        metrics = self.extract_metrics(data)

        if metrics["current_price"] is None:
            return "No data available"

        lines = []
        lines.append(f"Current Price: ${metrics['current_price']:.2f}")

        if metrics["market_maker_move"] and metrics["market_maker_move"] > 0:
            lines.append(f"Market Maker Move: ${metrics['market_maker_move']:.2f}")
            lines.append(f"Expected Range: ${metrics['lower_band']:.2f} - ${metrics['upper_band']:.2f}")

        if metrics["front_ex_move"] and metrics["front_ex_move"] > 0:
            lines.append(f"Front Expiration Move: ${metrics['front_ex_move']:.2f}")

        if metrics["back_ex_move"] and metrics["back_ex_move"] > 0:
            lines.append(f"Back Expiration Move: ${metrics['back_ex_move']:.2f}")

        return "\n".join(lines) if lines else "No move data available"
