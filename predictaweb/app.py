import fasthtml.common as fh
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()


def create_app():
    app = fh.FastHTML(hdrs=(fh.picolink,))

    class FormData(BaseModel):
        freq: str = "MS"
        horizon: int = 12
        finetune_steps: int = 0
        level: int = 90
        uploaded_file: str | None = None

    @app.route("/upload_file", methods=["POST"])
    async def upload_file(uploaded_file: fh.UploadFile):
        print(uploaded_file)
        contents = await uploaded_file.read()
        print(contents)
        return "ok"

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
                    fh.Input(id="uploaded_file", type="file"),
                    label="Upload your time series data (CSV format)",
                    cls="mb-2",
                    hx_post="/upload_file",
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(f"{__name__}:create_app", host="0.0.0.0", port=8000, reload=True)
