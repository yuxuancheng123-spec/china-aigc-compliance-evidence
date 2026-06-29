from src.generator import generate_synthetic_dataset
from src.label_metadata import generate_label_metadata, stable_hash


def test_label_metadata_generation_creates_one_record_per_output() -> None:
    dataset = generate_synthetic_dataset(seed=20260625, request_count=25)

    records, verification = generate_label_metadata(dataset)

    assert len(records) == len(dataset.outputs)
    assert len(verification["results"]) == len(dataset.outputs)
    first = records[0]
    assert first.label_id.startswith("LABEL-META-")
    assert first.output_hash_sha256
    assert first.metadata_hash_sha256
    assert first.machine_readable_format == "synthetic_metadata"


def test_hash_generation_is_deterministic() -> None:
    payload = {"request_id": "REQ-0001", "output_id": "OUT-0001", "synthetic": True}

    assert stable_hash(payload) == stable_hash({"synthetic": True, "output_id": "OUT-0001", "request_id": "REQ-0001"})
