import uuid
from dataclasses import dataclass
from io import BytesIO

import fasthtml.common as fh
import pandas as pd
from fh_plotly import plotly2fasthtml, plotly_headers
from utilsforecast.plotting import plot_series


def create_app():
    def scripts():
        return [
            fh.Script(
                """
                async function downloadFile(url) {
                    const response = await fetch(url);
                    const blob = await response.blob();
                    const urlObject = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = urlObject;
                    a.download = 'electricity.csv';  // Suggested file name
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    window.URL.revokeObjectURL(urlObject);
                }
                """
            )
        ]

    app = fh.FastHTML(hdrs=(fh.picolink, scripts(), *plotly_headers))

    @dataclass
    class ForecastParams:
        freq: str = "H"
        horizon: int = 24
        finetune_steps: int = 0
        level: int = 90

    @app.route("/forecast", methods=["POST"])
    def forecast(forecast_params: ForecastParams, session):
        if "df_filename" not in session:
            return fh.Div("Please upload data first")
        print(forecast_params)
        df = pd.read_csv(session["df_filename"])
        df["ds"] = pd.to_datetime(df["ds"])
        fig = plot_series(
            df,
            engine="plotly",
            max_insample_length=5 * forecast_params.horizon,
        )
        return plotly2fasthtml(fig)

    @app.route("/")
    async def post(uploaded_file: fh.UploadFile, session):
        contents = await uploaded_file.read()
        df = pd.read_csv(BytesIO(contents))
        random_filename = f"{uuid.uuid4()}.csv"
        df.to_csv(random_filename, index=False)
        session["df_filename"] = random_filename
        return fh.Div("Data uploaded")

    @app.route("/")
    def get(session):
        """Main page of the app."""
        forecast_params = ForecastParams()
        return fh.Div(
            fh.H1("Time Series Forecasting App"),
            fh.P(
                "👋 Welcome to Nixtla's forecasting app, your one-stop 🎯 solution for predicting your time series with precision powered by TimeGPT."
            ),
            fh.H2("Upload Data and Define Horizon"),
            fh.Div(
                fh.Div(
                    fh.Form(
                        fh.Group(
                            fh.Input(id="uploaded_file", type="file"),
                            fh.Button("Submit"),
                        ),
                        hx_post="/",
                        hx_swap="beforeend",
                        target_id="output_file",
                    ),
                    cls="mb-2",
                ),
                fh.Div(id="output_file"),
                fh.A(
                    fh.Button("Download Target Example Data"),
                    href="https://raw.githubusercontent.com/Nixtla/transfer-learning-time-series/main/datasets/electricity.csv",
                    download=None,
                    cls="text-blue-500",
                    onClick="event.preventDefault(); downloadFile('https://raw.githubusercontent.com/Nixtla/transfer-learning-time-series/main/datasets/electricity.csv')",
                ),
                cls="col-md-6",
            ),
            fh.H2("Forecasting parameters"),
            fh.Form(
                fh.Label(
                    "Define the frequency of your data (see ",
                    fh.A(
                        "pandas' available frequencies",
                        href="https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#offset-aliases",
                    ),
                    ")",
                    fh.Input(
                        type="text",
                        name="freq",
                        value=forecast_params.freq,
                        cls="input input-bordered w-full",
                    ),
                    cls="form-control mb-4 label-text p-6",
                ),
                fh.Label(
                    "Define forecast horizon (in number of timestamps you want to predict)",
                    fh.Input(
                        type="number",
                        name="horizon",
                        value=forecast_params.horizon,
                        cls="input input-bordered w-full",
                    ),
                    cls="form-control mb-4 label-text p-6",
                ),
                fh.Label(
                    "Define finetune steps (use zero for zero-shot inference, which is faster)",
                    fh.Input(
                        type="number",
                        name="finetune_steps",
                        value=forecast_params.finetune_steps,
                        cls="input input-bordered w-full",
                    ),
                    cls="form-control mb-4 label-text p-6",
                ),
                fh.Label(
                    "Define level for prediction intervals (uncertainty estimation)",
                    fh.Input(
                        type="number",
                        name="level",
                        value=forecast_params.level,
                        min="1",
                        max="99",
                        cls="input input-bordered w-full",
                    ),
                    cls="form-control mb-4 label-text p-6",
                ),
                fh.Button("Run Forecast", type="submit"),
                hx_post="/forecast",
                hx_swap="afterend",
                target_id="output",
            ),
            fh.Div(id="output", cls="col-md-6"),
            cls="container",
        )

    return app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(f"{__name__}:create_app", host="0.0.0.0", port=8000, reload=True)
