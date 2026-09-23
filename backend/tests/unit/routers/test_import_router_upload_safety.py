"""Upload safety tests for import router (M02: BE-002, BE-003, D10)."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from src.routers import import_router


def _fake_service():
    class _Fake:
        def upload_statement(self, save_path: str, filename: str, member: str = "Self"):
            assert (
                Path(save_path).resolve().parent == import_router.UPLOAD_DIR.resolve()
            )
            return {
                "success": True,
                "bank": "TestBank",
                "transaction_count": 0,
                "validation_status": "ok",
                "metadata": {},
                "log": [f"saved {member}"],
            }

        def detect_import_format(self, save_path: str):
            assert (
                Path(save_path).resolve().parent == import_router.UPLOAD_DIR.resolve()
            )
            return {
                "filename": Path(save_path).name,
                "columns": [],
                "sample_rows": [],
                "detected_mapping": {},
                "row_count": 0,
                "date_format": None,
                "skip_rows": 0,
            }

    return _Fake()


def _patch_service(monkeypatch) -> None:
    monkeypatch.setattr(import_router, "ImportService", lambda *a, **k: _fake_service())


def _cleanup(*names: str) -> None:
    for name in names:
        p = import_router.UPLOAD_DIR / name
        if p.exists():
            p.unlink()


class TestUploadStatementSafety:
    def test_traversal_filename_normalized_inside_upload_dir(
        self, client: TestClient, monkeypatch
    ) -> None:
        _patch_service(monkeypatch)
        try:
            response = client.post(
                "/api/upload",
                files={"file": ("../../evil.pdf", b"%PDF-1.4 fake", "application/pdf")},
            )
            assert response.status_code == 200
            assert (import_router.UPLOAD_DIR / "evil.pdf").exists()
        finally:
            _cleanup("evil.pdf")

    def test_disallowed_extension_rejected_on_upload(
        self, client: TestClient, monkeypatch
    ) -> None:
        _patch_service(monkeypatch)
        response = client.post(
            "/api/upload",
            files={"file": ("data.csv", b"Date,Amount\n", "text/csv")},
        )
        assert response.status_code in (400, 413, 500)
        assert "Only PDF files allowed" in response.text
        assert not (import_router.UPLOAD_DIR / "data.csv").exists()

    def test_oversized_payload_rejected_on_upload(
        self, client: TestClient, monkeypatch
    ) -> None:
        _patch_service(monkeypatch)
        monkeypatch.setenv("MAX_UPLOAD_SIZE_MB", "0")
        try:
            response = client.post(
                "/api/upload",
                files={"file": ("big.pdf", b"%PDF-1.4 fake", "application/pdf")},
            )
            # Small payload with a zero limit hits the explicit 413 check.
            assert response.status_code in (400, 413, 500)
            assert "File exceeds maximum upload size" in response.text
            assert not (import_router.UPLOAD_DIR / "big.pdf").exists()
        finally:
            _cleanup("big.pdf")

    def test_valid_small_pdf_still_succeeds(
        self, client: TestClient, monkeypatch
    ) -> None:
        _patch_service(monkeypatch)
        try:
            response = client.post(
                "/api/upload",
                files={"file": ("stmt.pdf", b"%PDF-1.4 fake", "application/pdf")},
            )
            assert response.status_code == 200
            body = response.json()
            assert body["success"] is True
            assert body["bank"] == "TestBank"
            assert body["transaction_count"] == 0
            assert "validation_status" in body
            assert "metadata" in body
            assert "log" in body
        finally:
            _cleanup("stmt.pdf")


class TestImportDetectSafety:
    def test_traversal_filename_normalized_inside_upload_dir(
        self, client: TestClient, monkeypatch
    ) -> None:
        _patch_service(monkeypatch)
        try:
            response = client.post(
                "/api/import/detect",
                files={"file": ("../../evil.csv", b"Date,Amount\n", "text/csv")},
            )
            assert response.status_code == 200
            assert (import_router.UPLOAD_DIR / "evil.csv").exists()
        finally:
            _cleanup("evil.csv")

    def test_disallowed_extension_rejected_on_detect(
        self, client: TestClient, monkeypatch
    ) -> None:
        _patch_service(monkeypatch)
        response = client.post(
            "/api/import/detect",
            files={"file": ("stmt.pdf", b"%PDF-1.4 fake", "application/pdf")},
        )
        assert response.status_code in (400, 413, 500)
        assert "Unsupported file type" in response.text
        assert not (import_router.UPLOAD_DIR / "stmt.pdf").exists()

    def test_oversized_payload_rejected_on_detect(
        self, client: TestClient, monkeypatch
    ) -> None:
        _patch_service(monkeypatch)
        monkeypatch.setenv("MAX_UPLOAD_SIZE_MB", "0")
        try:
            response = client.post(
                "/api/import/detect",
                files={"file": ("big.csv", b"Date,Amount\n", "text/csv")},
            )
            assert response.status_code in (400, 413, 500)
            assert "File exceeds maximum upload size" in response.text
            assert not (import_router.UPLOAD_DIR / "big.csv").exists()
        finally:
            _cleanup("big.csv")

    def test_valid_small_csv_still_succeeds(
        self, client: TestClient, monkeypatch
    ) -> None:
        _patch_service(monkeypatch)
        try:
            response = client.post(
                "/api/import/detect",
                files={"file": ("data.csv", b"Date,Amount\n", "text/csv")},
            )
            assert response.status_code == 200
            body = response.json()
            assert body["filename"] == "data.csv"
            assert body["row_count"] == 0
        finally:
            _cleanup("data.csv")
