import uuid
from dataclasses import dataclass
from io import BytesIO

import fasthtml.common as fh
import pandas as pd
from fh_plotly import plotly2fasthtml, plotly_headers
from nixtla import NixtlaClient
from utilsforecast.plotting import plot_series


def create_app():
    def hdrs():
        return [
            fh.Meta(charset="UTF-8"),
            fh.Meta(name="viewport", content="width=device-width, initial-scale=1.0"),
            fh.Meta(name="description", content="Forecasting App"),
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
            ),
            fh.Script(src="https://unpkg.com/htmx.org@2.0.2"),
            fh.Link(
                href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css",
                rel="stylesheet",
            ),
            fh.Link(
                href="https://cdn.jsdelivr.net/npm/daisyui@4.12.10/dist/full.css",
                rel="stylesheet",
            ),
        ]

    app = fh.FastHTML(hdrs=(hdrs(), *plotly_headers))

    @dataclass
    class ForecastParams:
        freq: str = "H"
        horizon: int = 24
        finetune_steps: int = 0
        level: int = 90
        nixtla_api_key: str = ""

    @app.route("/plot_data", methods=["POST"])
    def plot_data(forecast_params: ForecastParams, session):
        if "df_filename" not in session:
            return fh.Div("Please upload data first")

        df = pd.read_csv(session["df_filename"])
        df["ds"] = pd.to_datetime(df["ds"])
        client = NixtlaClient(api_key=forecast_params.nixtla_api_key)
        fcst_df = client.forecast(
            df,
            freq=forecast_params.freq,
            h=forecast_params.horizon,
            finetune_steps=forecast_params.finetune_steps,
            level=[forecast_params.level],
        )
        fig = plot_series(
            df,
            fcst_df,
            engine="plotly",
            level=[forecast_params.level],
        )
        return plotly2fasthtml(fig)

    @app.route("/")
    async def post(uploaded_file: fh.UploadFile, session):
        contents = await uploaded_file.read()
        df = pd.read_csv(BytesIO(contents))
        random_filename = f"{uuid.uuid4()}.csv"
        df.to_csv(random_filename, index=False)
        session["df_filename"] = random_filename
        return fh.Div("Data uploaded", cls="text-gray-300")

    @app.route("/")
    def get(session):
        """Main page of the app."""
        return fh.Div(
            # Title with a developer-focused vibe
            fh.H1(
                "🚀 Time Series Sandbox",
                cls="text-4xl font-bold text-green-500 mb-4",
            ),
            # Welcome message with dev-friendly tone
            fh.P(
                "💙 Welcome! You're about to enter the world of time series, powered by Nixtla. Let's do this!",
                cls="text-lg text-gray-300 mb-6",
            ),
            # Upload Data section with some developer flavor
            fh.H2(
                "⚡ Upload Your Data",
                cls="text-2xl text-blue-400 mt-6 mb-4",
            ),
            fh.Div(
                fh.Div(
                    fh.Form(
                        fh.Group(
                            fh.Input(
                                id="uploaded_file",
                                type="file",
                                cls="file-input file-input-bordered file-input-primary w-full max-w-xs",
                            ),
                            fh.Button("Upload", cls="btn btn-primary ml-2"),
                            fh.Div(id="output_file", cls="mt-2"),
                        ),
                        hx_post="/",
                        hx_swap="innerHTML",
                        target_id="output_file",
                        cls="flex items-center space-x-3",  # Flex layout for alignment
                    ),
                    cls="mb-2",
                ),
                fh.A(
                    fh.Button(
                        "Download Sample Data", cls="btn btn-xs btn-link text-blue-500"
                    ),  # Smaller, more subtle button
                    href="https://raw.githubusercontent.com/Nixtla/transfer-learning-time-series/main/datasets/electricity.csv",
                    download=None,
                    onClick="event.preventDefault(); downloadFile('https://raw.githubusercontent.com/Nixtla/transfer-learning-time-series/main/datasets/electricity.csv')",
                ),
                cls="mb-4",
            ),
            # Forecasting Parameters Section, styled for dev audience
            fh.H2(
                "🔧 Tune Your Forecast Settings", cls="text-2xl text-blue-400 mt-6 mb-4"
            ),
            fh.Form(
                fh.Div(
                    fh.Label(
                        "🔐 Add your Nixtla API key",
                        fh.A(
                            "Generate one",
                            href="https://dashboard.nixtla.io/",
                            cls="text-blue-500",
                        ),
                        cls="label text-gray-300 w-2/3",  # Label takes two-thirds of the width
                    ),
                    fh.Input(
                        type="text",
                        name="nixtla_api_key",
                        value="",
                        cls="input input-bordered w-1/3 bg-gray-800 text-white border-blue-500",  # Input takes one-third of the width
                    ),
                    cls="flex items-center mb-4",  # Flexbox for horizontal alignment
                ),
                # Frequency input with label and input side by side
                fh.Div(
                    fh.Label(
                        "🕒 Data Frequency (e.g., H for hourly, D for daily, etc.) ",
                        fh.A(
                            "Check Pandas' Offset Aliases",
                            href="https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#offset-aliases",
                            cls="text-blue-500",
                        ),
                        cls="label text-gray-300 w-2/3",  # Label takes two-thirds of the width
                    ),
                    fh.Input(
                        type="text",
                        name="freq",
                        value="MS",
                        cls="input input-bordered w-1/3 bg-gray-800 text-white border-blue-500",  # Input takes one-third of the width
                    ),
                    cls="flex items-center mb-4",  # Flexbox for horizontal alignment
                ),
                # Horizon input with label and input side by side
                fh.Div(
                    fh.Label(
                        "⏳ Forecast Horizon (How far into the future do you want to predict?)",
                        cls="label text-gray-300 w-2/3",  # Label takes two-thirds of the width
                    ),
                    fh.Input(
                        type="number",
                        name="horizon",
                        value=24,
                        cls="input input-bordered w-1/3 bg-gray-800 text-white border-blue-500",  # Input takes one-third of the width
                    ),
                    cls="flex items-center mb-4",  # Flexbox for horizontal alignment
                ),
                # Fine-tune steps input with label and input side by side
                fh.Div(
                    fh.Label(
                        "🚀 Fine-tune Steps (Go zero-shot for instant results, or take your time with custom finetuning)",
                        cls="label text-gray-300 w-2/3",  # Label takes two-thirds of the width
                    ),
                    fh.Input(
                        type="number",
                        name="finetune_steps",
                        value="0",
                        cls="input input-bordered w-1/3 bg-gray-800 text-white border-blue-500",  # Input takes one-third of the width
                    ),
                    cls="flex items-center mb-4",  # Flexbox for horizontal alignment
                ),
                # Prediction interval input with label and input side by side
                fh.Div(
                    fh.Label(
                        "📊 Prediction Interval (What’s your risk tolerance? Set between 1% and 99%)",
                        cls="label text-gray-300 w-2/3",  # Label takes two-thirds of the width
                    ),
                    fh.Input(
                        type="number",
                        name="level",
                        value="90",
                        min="1",
                        max="99",
                        cls="input input-bordered w-1/3 bg-gray-800 text-white border-blue-500",  # Input takes one-third of the width
                    ),
                    cls="flex items-center mb-4",  # Flexbox for horizontal alignment
                ),
                # Frequency input with dev-focused help text
                # Submit Button with more dynamic call to action
                fh.Button("🔮 Visualize", type="submit", cls="btn btn-success mt-4"),
                hx_post="/plot_data",
                hx_swap="afterend",
                target_id="output",
            ),
            # Forecast result output styled for devs
            fh.Div(id="output", cls="mt-6 text-yellow-300 font-mono"),
            # Overall page layout
            cls="container mx-auto p-8 bg-gray-900 text-white rounded-lg shadow-lg",
        )

    return app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(f"{__name__}:create_app", host="0.0.0.0", port=8000, reload=True)
else:
    import modal

    app = modal.App(name="forecasting-app-fasthtml")

    @app.function(
        image=modal.Image.debian_slim().pip_install_from_requirements(
            "requirements.txt"
        ),
        allow_concurrent_inputs=1000,
    )
    @modal.asgi_app()
    def serve():
        return create_app()
