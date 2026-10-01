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
                "/api/v1/upload",
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
            "/api/v1/upload",
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
                "/api/v1/upload",
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
                "/api/v1/upload",
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
                "/api/v1/import/detect",
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
            "/api/v1/import/detect",
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
                "/api/v1/import/detect",
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
                "/api/v1/import/detect",
                files={"file": ("data.csv", b"Date,Amount\n", "text/csv")},
            )
            assert response.status_code == 200
            body = response.json()
            assert body["filename"] == "data.csv"
            assert body["row_count"] == 0
        finally:
            _cleanup("data.csv")


class TestImportExecutePathContainment:
    """``/import/execute`` takes a filename in the request body, not as an upload.

    The two upload handlers confine the name to UPLOAD_DIR; ``import_execute``
    originally did not, so a request could name a path outside the upload
    directory and have the importer read it (CWE-22). These tests pin the
    containment on that route specifically.
    """

    @staticmethod
    def _payload(filename: str) -> dict:
        return {"filename": filename, "mapping": {}, "member": "Self"}

    def test_traversal_cannot_reach_a_file_outside_upload_dir(
        self, client: TestClient, monkeypatch
    ) -> None:
        """The real invariant: an outside file is never read.

        ``../../etc/passwd`` is reduced to ``passwd`` inside UPLOAD_DIR, so the
        request reports "not found" rather than 400. What matters is that the
        importer is never handed a path outside the upload directory, so this
        test plants a real file above UPLOAD_DIR and proves it is not read.
        """

        reached: list[str] = []

        class _Fake:
            def import_csv(self, save_path: str, mapping, member):
                reached.append(save_path)
                return {"success": True, "rows": 0, "log": []}

        monkeypatch.setattr(import_router, "ImportService", lambda *a, **k: _Fake())

        secret = import_router.UPLOAD_DIR.parent / "secret-outside.csv"
        secret.write_text("Date,Amount\n", encoding="utf-8")
        try:
            response = client.post(
                "/api/v1/import/execute",
                json=self._payload("../secret-outside.csv"),
            )
            assert response.status_code == 404, "outside file must not be importable"
            assert reached == [], "importer must not be invoked for an outside path"
        finally:
            secret.unlink(missing_ok=True)

    def test_dotdot_only_filename_is_rejected(self, client: TestClient) -> None:
        response = client.post("/api/v1/import/execute", json=self._payload(".."))
        assert response.status_code == 400
        assert "Invalid filename" in response.text

    def test_absolute_path_is_confined_to_upload_dir(
        self, client: TestClient, monkeypatch
    ) -> None:
        seen: dict[str, str] = {}

        class _Fake:
            def import_csv(self, save_path: str, mapping, member):
                seen["save_path"] = save_path
                return {"success": True, "rows": 0, "log": []}

        monkeypatch.setattr(import_router, "ImportService", lambda *a, **k: _Fake())
        target = import_router.UPLOAD_DIR / "outside.csv"
        target.write_text("Date,Amount\n", encoding="utf-8")
        try:
            response = client.post(
                "/api/v1/import/execute",
                json=self._payload(str(target)),
            )
            assert response.status_code == 200
            # The absolute path was reduced to its final component and confined.
            assert Path(seen["save_path"]).resolve().parent == (
                import_router.UPLOAD_DIR.resolve()
            )
        finally:
            target.unlink(missing_ok=True)

    def test_missing_file_still_reports_404(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/import/execute", json=self._payload("definitely-absent.csv")
        )
        assert response.status_code == 404
