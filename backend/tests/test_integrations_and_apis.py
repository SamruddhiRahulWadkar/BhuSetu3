import pytest
import json
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.integration.cadastral_adapter import CadastralGISAdapter
from backend.app.integration.lrms_adapter import LRMSAdapter
from backend.app.integration.dilrmp_mis_adapter import DILRMPMISAdapter
from backend.app.integration.webhook_service import WebhookService, WebhookSubscribeRequest
from backend.app.auth.security import create_access_token

client = TestClient(app)


def test_cadastral_gis_adapter():
    adapter = CadastralGISAdapter()
    parcels = adapter.get_all_parcels()
    assert parcels["type"] == "FeatureCollection"
    assert len(parcels["features"]) >= 10

    # ULPIN lookup
    sample_ulpin = parcels["features"][0]["properties"]["ulpin"]
    parcel = adapter.get_parcel_by_ulpin(sample_ulpin)
    assert parcel is not None
    assert parcel["properties"]["ulpin"] == sample_ulpin

    # Survey lookup
    p_by_survey = adapter.get_parcel_by_survey_no("Wagholi", "101")
    assert p_by_survey is not None
    assert p_by_survey["properties"]["survey_no"] == "101"


def test_lrms_adapter_hierarchy():
    adapter = LRMSAdapter()

    # Valid hierarchy
    valid_res = adapter.check_hierarchy(
        state="Maharashtra",
        district="Pune",
        tehsil="Haveli",
        village="Wagholi"
    )
    assert valid_res["valid"] is True

    # Invalid village hierarchy
    invalid_res = adapter.check_hierarchy(
        state="Maharashtra",
        district="Pune",
        tehsil="Haveli",
        village="NonExistentVillageXYZ"
    )
    assert invalid_res["valid"] is False


def test_dilrmp_mis_reporting():
    from backend.app.database import SessionLocal
    db = SessionLocal()
    try:
        report = DILRMPMISAdapter.generate_mis_dashboard_report(db)
        assert "programme" in report
        assert "dilrmp_kpis" in report
        assert "summary_metrics" in report
        assert report["dilrmp_kpis"]["maker_checker_compliance"] is not None

        ack = DILRMPMISAdapter.sync_to_central_portal(report)
        assert ack["sync_status"] == "success"
        assert ack["response_code"] == 200
    finally:
        db.close()


def test_webhook_subscription_and_signing():
    sub_req = WebhookSubscribeRequest(
        url="https://test-bank.internal/hooks",
        events=["RECORD_PUBLISHED"],
        secret="test-secret-key-123"
    )
    sub = WebhookService.register_subscription(sub_req)
    assert sub["id"].startswith("wh-")

    # Signature computation
    sig = WebhookService.compute_signature('{"test": 123}', "test-secret-key-123")
    assert len(sig) == 64  # SHA-256 hex string

    # Dispatch event
    deliveries = WebhookService.dispatch_event("RECORD_PUBLISHED", {"ulpin": "27HA1001000101"})
    assert len(deliveries) >= 1
    assert deliveries[-1]["status"] == "delivered"


def test_api_parcel_lookup():
    # Public / Auth lookup
    resp = client.get("/api/v1/parcels/27HA1001000101")
    assert resp.status_code == 200
    data = resp.json()
    assert data["type"] == "Feature"
    assert data["properties"]["ulpin"] == "27HA1001000101"

    # Non-existent parcel
    resp_404 = client.get("/api/v1/parcels/INVALID99999999")
    assert resp_404.status_code == 404


def test_api_records_export_formats():
    # 1. JSON Export
    resp_json = client.get("/api/v1/records/export?format=json")
    assert resp_json.status_code == 200
    j_data = resp_json.json()
    assert "records" in j_data
    assert "total_records" in j_data

    # 2. CSV Export
    resp_csv = client.get("/api/v1/records/export?format=csv")
    assert resp_csv.status_code == 200
    assert "text/csv" in resp_csv.headers["content-type"]
    assert "document_id" in resp_csv.text

    # 3. GeoJSON Export
    resp_geo = client.get("/api/v1/records/export?format=geojson")
    assert resp_geo.status_code == 200
    geo_data = resp_geo.json()
    assert geo_data["type"] == "FeatureCollection"


def test_api_dilrmp_and_webhooks():
    admin_token = create_access_token({"sub": "admin", "role": "admin"})
    headers = {"Authorization": f"Bearer {admin_token}"}

    # DILRMP Dashboard
    resp_dilrmp = client.get("/api/v1/integration/dilrmp-dashboard", headers=headers)
    assert resp_dilrmp.status_code == 200
    assert "summary_metrics" in resp_dilrmp.json()

    # DILRMP Sync
    resp_sync = client.post("/api/v1/integration/dilrmp-sync", headers=headers)
    assert resp_sync.status_code == 200
    assert resp_sync.json()["sync_status"] == "success"

    # Webhook test dispatch
    resp_hook = client.post(
        "/api/v1/integration/webhooks/test-dispatch",
        json={"event": "RECORD_PUBLISHED", "document_id": "doc-01"},
        headers=headers
    )
    assert resp_hook.status_code == 200
    assert resp_hook.json()["dispatched_count"] >= 1
