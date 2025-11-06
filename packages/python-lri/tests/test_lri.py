"""
LRI class tests for python-lri
"""

import base64
import json
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from fastapi import FastAPI, Request

from lri import LRI, LCE, Intent, Policy


class TestLRI:
    """Test LRI class"""

    def test_init_default(self):
        """Test LRI initialization with defaults"""
        lri = LRI()
        assert lri.header_name == "LCE"
        assert lri.validate is True

    def test_init_custom(self):
        """Test LRI initialization with custom params"""
        lri = LRI(header_name="X-Custom-LCE", validate=False)
        assert lri.header_name == "X-Custom-LCE"
        assert lri.validate is False


class TestParseRequest:
    """Test LRI.parse_request method"""

    @pytest.fixture
    def app(self):
        """Create test FastAPI app"""
        app = FastAPI()
        return app

    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return TestClient(app)

    @pytest.fixture
    def lri(self):
        """Create LRI instance"""
        return LRI()

    def test_parse_valid_lce(self, app, client, lri):
        """Test parsing valid LCE from request"""

        @app.get("/test")
        async def test_endpoint(request: Request):
            lce = await lri.parse_request(request)
            return {"ok": True, "intent": lce.intent.type if lce else None}

        # Create valid LCE
        lce_data = {
            "v": 1,
            "intent": {"type": "ask"},
            "policy": {"consent": "private"},
        }
        b64 = base64.b64encode(json.dumps(lce_data).encode()).decode()

        response = client.get("/test", headers={"LCE": b64})
        assert response.status_code == 200
        assert response.json()["intent"] == "ask"

    def test_parse_missing_lce_not_required(self, app, client, lri):
        """Test parsing when LCE is missing and not required"""

        @app.get("/test")
        async def test_endpoint(request: Request):
            lce = await lri.parse_request(request, required=False)
            return {"ok": True, "has_lce": lce is not None}

        response = client.get("/test")
        assert response.status_code == 200
        assert response.json()["has_lce"] is False

    def test_parse_missing_lce_required(self, app, client, lri):
        """Test parsing when LCE is missing and required"""

        @app.get("/test")
        async def test_endpoint(request: Request):
            lce = await lri.parse_request(request, required=True)
            return {"ok": True}

        response = client.get("/test")
        assert response.status_code == 428
        assert "LCE header required" in response.json()["detail"]["error"]

    def test_parse_malformed_base64(self, app, client, lri):
        """Test parsing malformed Base64"""

        @app.get("/test")
        async def test_endpoint(request: Request):
            lce = await lri.parse_request(request)
            return {"ok": True}

        response = client.get("/test", headers={"LCE": "not-valid-base64!!!"})
        assert response.status_code == 400
        assert "Malformed LCE header" in response.json()["detail"]["error"]

    def test_parse_invalid_json(self, app, client, lri):
        """Test parsing invalid JSON"""

        @app.get("/test")
        async def test_endpoint(request: Request):
            lce = await lri.parse_request(request)
            return {"ok": True}

        b64 = base64.b64encode(b"not json").decode()
        response = client.get("/test", headers={"LCE": b64})
        assert response.status_code == 400

    def test_parse_invalid_lce_schema(self, app, client, lri):
        """Test parsing LCE that fails schema validation"""

        @app.get("/test")
        async def test_endpoint(request: Request):
            lce = await lri.parse_request(request)
            return {"ok": True}

        # Missing required fields
        lce_data = {"v": 1, "intent": {"type": "ask"}}  # Missing policy
        b64 = base64.b64encode(json.dumps(lce_data).encode()).decode()

        response = client.get("/test", headers={"LCE": b64})
        assert response.status_code == 422
        assert "Invalid LCE" in response.json()["detail"]["error"]

    def test_parse_custom_header_name(self, app, client):
        """Test parsing with custom header name"""
        lri = LRI(header_name="X-Custom-LCE")

        @app.get("/test")
        async def test_endpoint(request: Request):
            lce = await lri.parse_request(request)
            return {"ok": True, "intent": lce.intent.type if lce else None}

        lce_data = {
            "v": 1,
            "intent": {"type": "tell"},
            "policy": {"consent": "private"},
        }
        b64 = base64.b64encode(json.dumps(lce_data).encode()).decode()

        response = client.get("/test", headers={"X-Custom-LCE": b64})
        assert response.status_code == 200
        assert response.json()["intent"] == "tell"

    def test_parse_validation_disabled(self, app, client):
        """Test parsing with validation disabled"""
        lri = LRI(validate=False)

        @app.get("/test")
        async def test_endpoint(request: Request):
            lce = await lri.parse_request(request)
            return {"ok": True}

        # Invalid LCE (missing policy)
        lce_data = {"v": 1, "intent": {"type": "ask"}}
        b64 = base64.b64encode(json.dumps(lce_data).encode()).decode()

        # With validation disabled, this should fail at Pydantic level
        response = client.get("/test", headers={"LCE": b64})
        assert response.status_code == 422


class TestCreateHeader:
    """Test LRI.create_header static method"""

    def test_create_header_minimal(self):
        """Test creating header from minimal LCE"""
        lce = LCE(
            v=1, intent=Intent(type="tell"), policy=Policy(consent="private")
        )

        header = LRI.create_header(lce)

        # Should be valid Base64
        decoded = base64.b64decode(header).decode()
        data = json.loads(decoded)

        assert data["v"] == 1
        assert data["intent"]["type"] == "tell"
        assert data["policy"]["consent"] == "private"

    def test_create_header_full(self):
        """Test creating header from full LCE"""
        lce = LCE(
            v=1,
            intent=Intent(type="ask", goal="Test"),
            policy=Policy(consent="team", share=["service-1"]),
        )

        header = LRI.create_header(lce)
        decoded = base64.b64decode(header).decode()
        data = json.loads(decoded)

        assert data["intent"]["goal"] == "Test"
        assert data["policy"]["share"] == ["service-1"]

    def test_create_header_idempotent(self):
        """Test creating header is idempotent"""
        lce = LCE(
            v=1, intent=Intent(type="tell"), policy=Policy(consent="private")
        )

        header1 = LRI.create_header(lce)
        header2 = LRI.create_header(lce)

        assert header1 == header2

    def test_create_header_excludes_none(self):
        """Test header excludes None values"""
        lce = LCE(
            v=1, intent=Intent(type="tell"), policy=Policy(consent="private")
        )

        header = LRI.create_header(lce)
        decoded = base64.b64decode(header).decode()
        data = json.loads(decoded)

        # Optional fields should not be in JSON
        assert "affect" not in data
        assert "meaning" not in data
        assert "qos" not in data
