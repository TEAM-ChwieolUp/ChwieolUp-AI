from fastapi import FastAPI


app = FastAPI(title="ChwieolUp AI Server")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


# TODO: Include feature routers after API schemas and services are implemented.
