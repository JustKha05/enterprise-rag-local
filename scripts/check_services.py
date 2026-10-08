import json
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from app.config import settings


def get_json(url: str) -> dict:
    with urlopen(url, timeout=10) as response:
        return json.load(response)


def main() -> None:
    errors = []

    # Check Qdrant.
    try:
        result = get_json(
            f"{settings.qdrant_url.rstrip('/')}/collections"
        )
        collections = result["result"]["collections"]

        print(f"OK: Qdrant connected at {settings.qdrant_url}")
        print(f"Collections: {len(collections)}")

    except (HTTPError, URLError, TimeoutError, ValueError, KeyError) as exc:
        errors.append(f"Qdrant: {exc}")
        print(f"ERROR: Qdrant check failed: {exc}")

    # Check Ollama and the configured model.
    try:
        result = get_json(
            f"{settings.ollama_url.rstrip('/')}/api/tags"
        )
        model_names = [
            model["name"]
            for model in result["models"]
        ]

        print(f"OK: Ollama connected at {settings.ollama_url}")
        print(f"Installed models: {', '.join(model_names) or '(none)'}")

        if settings.generation_model in model_names:
            print(f"OK: Model available: {settings.generation_model}")
        else:
            message = (
                f"Configured model is missing: "
                f"{settings.generation_model}"
            )
            errors.append(message)
            print(f"ERROR: {message}")

    except (HTTPError, URLError, TimeoutError, ValueError, KeyError) as exc:
        errors.append(f"Ollama: {exc}")
        print(f"ERROR: Ollama check failed: {exc}")

    if errors:
        raise SystemExit(1)

    print("OK: All service checks passed.")


if __name__ == "__main__":
    main()