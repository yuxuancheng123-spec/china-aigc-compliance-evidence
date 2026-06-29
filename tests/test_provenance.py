from src.generator import generate_synthetic_dataset
from src.label_metadata import generate_label_metadata
from src.provenance import generate_provenance_manifests


def test_provenance_manifest_generation_includes_required_events() -> None:
    dataset = generate_synthetic_dataset(seed=20260625, request_count=10)
    labels, _ = generate_label_metadata(dataset)

    manifests = generate_provenance_manifests(dataset, labels)

    assert len(manifests) == len(dataset.generation_requests)
    event_types = {event.event_type for event in manifests[0].events}
    assert {
        "request_created",
        "consent_validated",
        "model_filing_checked",
        "output_generated",
        "label_attached",
        "content_safety_checked",
        "complaint_checked",
        "assessment_completed",
    }.issubset(event_types)
