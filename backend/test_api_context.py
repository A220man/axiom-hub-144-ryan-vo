"""
Tests for Context API Endpoints
"""

import json
import tempfile
import shutil
from pathlib import Path
import pytest
from httpx import AsyncClient, ASGITransport

from main import app


class TestContextAPI:
    """Tests for context API endpoints."""

    def setup_method(self):
        """Create a temporary directory for each test."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.project_root = self.temp_dir / "project"
        self.project_root.mkdir()
        self.original_cwd = Path.cwd()
        import os
        os.chdir(self.project_root)

    def teardown_method(self):
        """Clean up temporary directory."""
        import os
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_resolve_context_no_files(self):
        """Test resolving context when no files exist."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/context/resolve")
            assert response.status_code == 200
            data = response.json()
            assert data["product"] is None
            assert data["design"] is None
            assert data["config_path"] is None

    @pytest.mark.asyncio
    async def test_resolve_context_with_files(self):
        """Test resolving context with default files."""
        (self.project_root / "PRODUCT.md").write_text("# Product")
        (self.project_root / "DESIGN.md").write_text("# Design")
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/context/resolve")
            assert response.status_code == 200
            data = response.json()
            assert data["product"] is not None
            assert data["design"] is not None
            assert "PRODUCT.md" in data["product"]
            assert "DESIGN.md" in data["design"]

    @pytest.mark.asyncio
    async def test_validate_context_success(self):
        """Test validation with valid files."""
        (self.project_root / "PRODUCT.md").write_text("# Product")
        (self.project_root / "DESIGN.md").write_text("# Design")
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/context/validate")
            assert response.status_code == 200
            data = response.json()
            assert data["valid"] is True
            assert len(data["errors"]) == 0
            assert data["paths"]["product"] is not None
            assert data["paths"]["design"] is not None

    @pytest.mark.asyncio
    async def test_validate_context_missing_files(self):
        """Test validation when files are missing."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/context/validate")
            assert response.status_code == 200
            data = response.json()
            assert data["valid"] is True  # Missing files are warnings
            assert len(data["warnings"]) == 2

    @pytest.mark.asyncio
    async def test_get_context_config_empty(self):
        """Test getting config when none exists."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/context/config")
            assert response.status_code == 200
            data = response.json()
            assert data["product"] is None
            assert data["design"] is None

    @pytest.mark.asyncio
    async def test_create_context_config(self):
        """Test creating a context config file."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/context/config",
                json={"product": "governance/product.md", "design": "docs/design.md"}
            )
            assert response.status_code == 200
            data = response.json()
            assert "config_path" in data
            assert "context.json" in data["config_path"]
            
            # Verify the file was created
            config_path = self.project_root / "context.json"
            assert config_path.exists()
            
            with open(config_path) as f:
                config_data = json.load(f)
            assert config_data["contextFiles"]["product"] == "governance/product.md"
            assert config_data["contextFiles"]["design"] == "docs/design.md"

    @pytest.mark.asyncio
    async def test_get_context_config_after_create(self):
        """Test getting config after creating it."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Create config
            await client.post(
                "/api/context/config",
                json={"product": "custom/product.md", "design": "custom/design.md"}
            )
            
            # Get config
            response = await client.get("/api/context/config")
            assert response.status_code == 200
            data = response.json()
            assert data["product"] == "custom/product.md"
            assert data["design"] == "custom/design.md"

    @pytest.mark.asyncio
    async def test_resolve_with_config_file(self):
        """Test resolving with explicit config file."""
        (self.project_root / "custom" / "product.md").parent.mkdir(parents=True)
        (self.project_root / "custom" / "product.md").write_text("# Custom Product")
        (self.project_root / "brand" / "design.md").parent.mkdir(parents=True)
        (self.project_root / "brand" / "design.md").write_text("# Brand Design")
        
        config_data = {
            "contextFiles": {
                "product": "custom/product.md",
                "design": "brand/design.md"
            }
        }
        (self.project_root / "context.json").write_text(json.dumps(config_data))
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/context/resolve")
            assert response.status_code == 200
            data = response.json()
            assert data["product"] is not None
            assert data["design"] is not None
            assert "custom/product.md" in data["product"]
            assert "brand/design.md" in data["design"]

    @pytest.mark.asyncio
    async def test_validate_with_invalid_config(self):
        """Test validation with invalid configured path."""
        config_data = {
            "contextFiles": {
                "product": "nonexistent/product.md"
            }
        }
        (self.project_root / "context.json").write_text(json.dumps(config_data))
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/context/validate")
            assert response.status_code == 200
            data = response.json()
            assert data["valid"] is False
            assert len(data["errors"]) == 1
            assert "Product path" in data["errors"][0]
