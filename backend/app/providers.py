import json
from pathlib import Path

from app.database import PROJECT_ROOT

FIXTURE_PATH = PROJECT_ROOT / "data" / "fixtures" / "demo_responses_v1.json"


class ProviderUnavailable(Exception):
    """Raised when the chosen execution mode cannot run. Never silently falls back to another mode."""


class DemoProvider:
    mode = "demo"
    is_simulated = True
    model_name = "demo-fixtures-v1 (SIMULATED - not a language model)"

    def __init__(self, dataset_name: str, dataset_version: str, fixture_path: Path = FIXTURE_PATH):
        if not fixture_path.exists():
            raise ProviderUnavailable(f"Demo fixture file not found: {fixture_path}")
        data = json.loads(fixture_path.read_text(encoding="utf-8"))
        if data["dataset_name"] != dataset_name or data["dataset_version"] != dataset_version:
            raise ProviderUnavailable(
                f"Demo fixtures were written only for {data['dataset_name']} {data['dataset_version']}, "
                f"not {dataset_name} {dataset_version}."
            )
        self.answers = data["answers"]
        self.fixture_file = fixture_path.name

    def generate(self, strategy: str, external_id: str, prompt: str) -> str:
        # The prompt is built and recorded by the runner but not used here:
        # demo mode only looks up the predefined fixture answer.
        try:
            return self.answers[external_id][strategy]
        except KeyError:
            raise ProviderUnavailable(f"No demo fixture for {external_id} / {strategy}")


def get_provider(mode: str, dataset_name: str, dataset_version: str):
    if mode == "demo":
        return DemoProvider(dataset_name, dataset_version)
    if mode in ("local_llm", "external_api"):
        raise ProviderUnavailable(
            f"Execution mode '{mode}' is not implemented yet. The system does not fall back to demo mode automatically."
        )
    raise ProviderUnavailable(f"Unknown execution mode: {mode}")