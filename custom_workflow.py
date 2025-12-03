import re
import asyncio
from typing import List, Dict, Any

import pandas as pd

from vanna.core.workflow.base import WorkflowHandler, WorkflowResult
from vanna.components import UiComponent, DataFrameComponent, ChartComponent, StatusBarUpdateComponent, RichTextComponent
from vanna.integrations.plotly import PlotlyChartGenerator


class CustomWorkflow(WorkflowHandler):
    """
    Intercepts a specific demo question and returns mock results and a chart
    without executing the SQL runner.
    """

    _PATTERN = re.compile(
        r"from\s+elegance,\s*amd\s*and\s*emulsion.*bmi\s+is\s+greater\s+than\s+27\.5.*1:1\s*amd\s*healthy\s*control",
        re.IGNORECASE | re.DOTALL,
    )

    def _build_records(self) -> List[Dict[str, Any]]:
        # Columns expected by FE tables in this project
        cols = [
            "subject_id",
            "gender",
            "age_no",
            "race",
            "sequencing_id",
            "hypertension_ind",
            "systolic_blood_pressure_val",
            "diastolic_blood_pressure_val",
            "diabetes_ind",
            "hba1c_val",
            "obese_ind",
            "bmi_val",
            "hyperlipidaemia_ind",
            "total_cholesterol_val",
            "triglyceride_val",
            "health_status",
            "dataset_source",
        ]

        def r(
            subject_id: str,
            gender: str,
            age_no: int,
            race: str,
            sequencing_id: str,
            hypertension: int,
            diabetes: int,
            obese_ind: str,
            bmi: float,
            hyperlipidaemia: int,
            dataset_source: str,
        ) -> Dict[str, Any]:
            return {
                "subject_id": subject_id,
                "gender": gender,
                "age_no": age_no,
                "race": race,
                "sequencing_id": sequencing_id,
                "hypertension_ind": hypertension,
                "systolic_blood_pressure_val": None,
                "diastolic_blood_pressure_val": None,
                "diabetes_ind": diabetes,
                "hba1c_val": None,
                "obese_ind": obese_ind,
                "bmi_val": bmi,
                "hyperlipidaemia_ind": hyperlipidaemia,
                "total_cholesterol_val": None,
                "triglyceride_val": None,
                "health_status": "Unhealthy",
                "dataset_source": dataset_source,
            }

        records: List[Dict[str, Any]] = [
            r("FLV118", "Female", 23, "Chinese", "B18FLV118", 0, 0, "Obese", 35.96, 0, "EMULSION"),
            r("AMD0808", "Female", 25, "Chinese", "B15AMD0808", 0, 0, "Obese", 29.74, 0, "AMD"),
            r("AMD1033", "Female", 26, "Chinese", "B046AMD1033", 0, 0, "Obese", 28.65, 0, "AMD"),
            r("FLV047", "Female", 26, "Chinese", "B18FLV047", 0, 0, "Obese", 34.73, 0, "EMULSION"),
            r("AMD1421", "Female", 27, "Chinese", "B080AMD1421", 0, 0, "Obese", 31.64, 0, "AMD"),
            r("AMD1542", "Female", 28, "Chinese", "DNFA5DPSHKJJ", 0, 0, "Obese", 29.05, 0, "AMD"),
            r("AMD0821", "Female", 28, "Chinese", "B15AMD0821", 0, 0, "Obese", 32.66, 0, "AMD"),
            r("AMD1190", "Female", 28, "Chinese", "B048AMD1190", 0, 0, "Obese", 34.63, 0, "AMD"),
            r("FLV087", "Female", 28, "Chinese", "B18FLV087", 0, 0, "Obese", 63.23, 0, "EMULSION"),
            r("AMD0806", "Female", 28, "Chinese", "B16AMD0806", 0, 0, "Obese", 30.48, 0, "AMD"),
            r("AMD0323", "Female", 29, "Chinese", "B05AML_AMD_0323", 0, 0, "Obese", 37.59, 1, "AMD"),
            r("NEMB060", "Female", 29, "Chinese", "B00721S15692", 0, 0, "Obese", 46.65, 0, "EMULSION"),
            r("NEMB027", "Female", 29, "Chinese", "B00720S36898", 0, 0, "Obese", 46.71, 0, "EMULSION"),
            r("NEMB052", "Female", 30, "Chinese", "B00721S07627", 1, 1, "Obese", 33.92, 1, "EMULSION"),
            r("AMD0694", "Female", 30, "Chinese", "B13AMD0694", 0, 0, "Obese", 28.28, 0, "AMD"),
            r("AMD1380", "Female", 30, "Chinese", "B079AMD1380", 0, 0, "Obese", 31.11, 0, "AMD"),
            r("AMD0617", "Female", 30, "Chinese", "B13AMD0617", 0, 0, "Obese", 31.18, 0, "AMD"),
            r("AMD0712", "Female", 30, "Chinese", "B13AMD0712", 0, 0, "Obese", 32.02, 0, "AMD"),
            r("AMD1102", "Female", 31, "Chinese", "B047AMD1102", 0, 0, "Obese", 29.74, 0, "AMD"),
            r("AMD1067", "Female", 31, "Chinese", "B010AMD1067", 0, 0, "Obese", 30.11, 0, "AMD"),
        ]

        # Ensure column order
        normalized: List[Dict[str, Any]] = [{k: rec.get(k) for k in cols} for rec in records]
        return normalized

    async def try_handle(self, agent, user, conversation, message: str) -> WorkflowResult:
        if not self._PATTERN.search(message or ""):
            return WorkflowResult(should_skip_llm=False)

        # Build mock top-20 records
        records = self._build_records()

        # Create table component (top 20)
        df_component = DataFrameComponent.from_records(
            records,
            title="Unhealthy cohort + matched controls (top 20)",
            description=None,
            page_size=20,
            paginated=True,
            max_rows_displayed=20,
        )

        # Create a simple BMI distribution chart using Plotly
        df = pd.DataFrame(records)
        bmi_df = df[["bmi_val"]].copy()
        bmi_df = bmi_df.rename(columns={"bmi_val": "BMI"})
        chart = PlotlyChartGenerator().generate_chart(bmi_df, "BMI distribution (top 20)")
        chart_component = ChartComponent(chart_type="plotly", data=chart, title="BMI distribution (top 20)")

        async def stream():
            # Simulate lightweight "thinking" steps
            yield UiComponent(
                rich_component=StatusBarUpdateComponent(
                    status="working",
                    message="Analyzing request...",
                    detail="Building cohort and matching controls",
                ),
                simple_component=None,
            )
            await asyncio.sleep(1.2)
            yield UiComponent(
                rich_component=StatusBarUpdateComponent(
                    status="working",
                    message="Preparing results...",
                    detail="Formatting table and chart",
                ),
                simple_component=None,
            )
            await asyncio.sleep(1.0)
            yield UiComponent(
                rich_component=StatusBarUpdateComponent(
                    status="working",
                    message="Almost ready...",
                    detail="Applying display options",
                ),
                simple_component=None,
            )
            await asyncio.sleep(0.8)

            # Show table then chart
            yield UiComponent(rich_component=df_component, simple_component=None)
            yield UiComponent(rich_component=chart_component, simple_component=None)
            yield UiComponent(
                rich_component=StatusBarUpdateComponent(
                    status="idle",
                    message="Response complete",
                    detail="Ready for next message",
                ),
                simple_component=None,
            )

        return WorkflowResult(should_skip_llm=True, components=stream())


