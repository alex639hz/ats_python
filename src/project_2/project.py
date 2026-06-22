import json
import logging
from pathlib import Path
from statistics import mean
from typing import TYPE_CHECKING, Any

from engine.constants import DEF_OK, LABEL_NAME, NOARG
from engine.procedure_builder import ProcedureBuilder
from engine.types import StepInterface
from engine.utils import Utils

if TYPE_CHECKING:
    from engine.framework import Framework


logger = logging.getLogger("[stock_analytics]")

PROJECT_FOLDER = Path("C:/ats_python/src/project_2")
OUTPUT_FOLDER = PROJECT_FOLDER / "output"


class Project2:
    """Stock trading analytics project using the existing procedure framework."""

    def __init__(self, framework: "Framework") -> None:
        self.framework = framework
        self.cases = Utils.read_json(PROJECT_FOLDER / "test_cases.json")
        self.market_data = Utils.read_json(PROJECT_FOLDER / "market_data.json")

    def export(self):
        builder = ProcedureBuilder("stock_analytics")
        builder.add_step_function(self.runtime_create_session, NOARG, LABEL_NAME)
        builder.add_step_function(self.runtime_analyze_cases, NOARG, LABEL_NAME)
        builder.add_step_function(self.runtime_export_report, NOARG, LABEL_NAME)

        procedure = builder.generate_procedure().start()
        self.framework.procedure_append(procedure)

    def runtime_create_session(self, step_interface: StepInterface):
        procedure, args = Utils.extract_step_interface(step_interface)
        session = {
            "created_at": self.framework.get_time_datetime().isoformat(),
            "label": procedure.get_label(),
            "cases_count": len(self.cases),
            "symbols": sorted(self.market_data.keys()),
        }
        procedure.context.attribute_set("session", session)
        procedure.context.attribute_set("cases", self.cases)
        procedure.context.attribute_set("market_data", self.market_data)
        return DEF_OK

    def runtime_analyze_cases(self, step_interface: StepInterface):
        procedure, args = Utils.extract_step_interface(step_interface)
        cases: list[dict[str, Any]] = procedure.context.attribute_get("cases", [])
        market_data: dict[str, list[dict[str, Any]]] = procedure.context.attribute_get(
            "market_data", {}
        )

        results = []
        for case in cases:
            symbol = case["symbol"]
            candles = market_data.get(symbol, [])
            result = self._analyze_symbol(symbol, candles, case)
            results.append(result)

        procedure.context.attribute_set("results", results)
        return DEF_OK

    def runtime_export_report(self, step_interface: StepInterface):
        procedure, args = Utils.extract_step_interface(step_interface)
        session = procedure.context.attribute_get("session")
        results = procedure.context.attribute_get("results", [])

        report = {
            "session": session,
            "summary": self._summarize_results(results),
            "results": results,
        }

        OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
        output_file = OUTPUT_FOLDER / "latest_report.json"
        Utils.atomic_file_write_text(output_file, json.dumps(report, indent=2))

        procedure.context.attribute_set("report", report)
        procedure.context.attribute_set("report_path", str(output_file))
        logger.info("stock analytics report exported: %s", output_file)
        return DEF_OK

    @staticmethod
    def _analyze_symbol(
        symbol: str, candles: list[dict[str, Any]], case: dict[str, Any]
    ) -> dict[str, Any]:
        if not candles:
            return {
                "symbol": symbol,
                "label": case["label"],
                "signal": "NO_DATA",
                "reason": "No market data found for symbol",
            }

        closes = [float(candle["close"]) for candle in candles]
        latest_close = closes[-1]
        short_window = int(case.get("short_window", 3))
        long_window = int(case.get("long_window", 5))
        momentum_window = int(case.get("momentum_window", 3))

        short_ma = Project2._window_mean(closes, short_window)
        long_ma = Project2._window_mean(closes, long_window)
        momentum = Project2._momentum(closes, momentum_window)
        signal = Project2._signal_from_metrics(short_ma, long_ma, momentum, case)

        return {
            "symbol": symbol,
            "label": case["label"],
            "latest_close": latest_close,
            "short_ma": short_ma,
            "long_ma": long_ma,
            "momentum_pct": momentum,
            "signal": signal,
        }

    @staticmethod
    def _window_mean(values: list[float], window: int) -> float:
        if window <= 0:
            raise ValueError("window must be greater than zero")
        selected = values[-window:]
        return round(mean(selected), 4)

    @staticmethod
    def _momentum(values: list[float], window: int) -> float:
        if window <= 0:
            raise ValueError("window must be greater than zero")
        if len(values) <= window:
            return 0.0

        previous = values[-window - 1]
        latest = values[-1]
        if previous == 0:
            return 0.0
        return round(((latest - previous) / previous) * 100, 4)

    @staticmethod
    def _signal_from_metrics(
        short_ma: float, long_ma: float, momentum: float, case: dict[str, Any]
    ) -> str:
        buy_threshold = float(case.get("buy_momentum_pct", 1.0))
        sell_threshold = float(case.get("sell_momentum_pct", -1.0))

        if short_ma > long_ma and momentum >= buy_threshold:
            return "BUY"
        if short_ma < long_ma and momentum <= sell_threshold:
            return "SELL"
        return "HOLD"

    @staticmethod
    def _summarize_results(results: list[dict[str, Any]]) -> dict[str, int]:
        summary = {"BUY": 0, "SELL": 0, "HOLD": 0, "NO_DATA": 0}
        for result in results:
            signal = result.get("signal", "NO_DATA")
            summary[signal] = summary.get(signal, 0) + 1
        return summary
