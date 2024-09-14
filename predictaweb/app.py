from io import BytesIO

import fasthtml.common as fh
import pandas as pd
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()


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

    app = fh.FastHTML(hdrs=(fh.picolink, scripts()))

    class FormData(BaseModel):
        freq: str = "MS"
        horizon: int = 12
        finetune_steps: int = 0
        level: int = 90
        uploaded_file: str | None = None

    @app.route("/upload_file", methods=["POST"])
    async def upload_file(uploaded_file: fh.UploadFile, session):
        contents = await uploaded_file.read()
        df = pd.read_csv(BytesIO(contents))
        session["df"] = df.to_json(orient="split")

    @app.route("/")
    def index(request, session):
        """Main page of the app."""
        if "processed" not in session:
            session["processed"] = {}
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
                        hx_post="/upload_file",
                        hx_swap="none",
                    ),
                    cls="mb-2",
                ),
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
            fh.Div(
                fh.Div(
                    fh.Input(type="text", name="freq", value="MS"),
                    label="Define the frequency of your data (see pandas' available frequencies)",
                    cls="col-md-3",
                ),
                fh.Div(
                    fh.Input(type="number", name="horizon", value="12"),
                    label="Define forecast horizon (in number of timestamps you want to predict)",
                    cls="col-md-3",
                ),
                fh.Div(
                    fh.Input(type="number", name="finetune_steps", value="0"),
                    label="Define finetune steps (use zero for zero-shot inference, which is faster)",
                    cls="col-md-3",
                ),
                fh.Div(
                    fh.Input(
                        type="number", name="level", value="90", min="1", max="99"
                    ),
                    label="Define level for prediction intervals (uncertainty estimation)",
                    cls="col-md-3",
                ),
                cls="row mb-3",
            ),
            fh.Button("Run Forecast", type="submit"),
            cls="container",
            method="post",
        )

    return app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(f"{__name__}:create_app", host="0.0.0.0", port=8000, reload=True)
