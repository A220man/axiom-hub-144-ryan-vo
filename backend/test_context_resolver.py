"""
Tests for Context Resolver Module
"""

import os
import json
import tempfile
import shutil
from pathlib import Path
import pytest

from context_resolver import (
    DesignSidecar,
    StalenessResult,
    ContextFilesConfig,
    ResolvedPaths,
    ContextResolver,
    create_default_config,
)


class TestContextFilesConfig:
    """Tests for ContextFilesConfig dataclass."""

    def test_default_config(self):
        config = ContextFilesConfig()
        assert config.product is None
        assert config.design is None

    def test_config_with_paths(self):
        config = ContextFilesConfig(product="governance/product.md", design="docs/design.md")
        assert config.product == "governance/product.md"
        assert config.design == "docs/design.md"

    def test_to_dict(self):
        config = ContextFilesConfig(product="product.md", design="design.md")
        data = config.to_dict()
        assert data == {"product": "product.md", "design": "design.md"}

    def test_from_dict(self):
        data = {"product": "product.md", "design": "design.md"}
        config = ContextFilesConfig.from_dict(data)
        assert config.product == "product.md"
        assert config.design == "design.md"

    def test_from_dict_partial(self):
        data = {"product": "product.md"}
        config = ContextFilesConfig.from_dict(data)
        assert config.product == "product.md"
        assert config.design is None


class TestContextResolver:
    """Tests for ContextResolver class."""

    def setup_method(self):
        """Create a temporary directory for each test."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.project_root = self.temp_dir / "project"
        self.project_root.mkdir()
        self.resolver = ContextResolver(self.project_root)

    def teardown_method(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_discover_product_default_name(self):
        """Test discovery of PRODUCT.md in project root."""
        (self.project_root / "PRODUCT.md").write_text("# Product")
        path = self.resolver.resolve_product_path()
        assert path is not None
        assert path.name == "PRODUCT.md"

    def test_discover_product_case_variants(self):
        """Test discovery with different case variants."""
        for name in ["product.md", "Product.md"]:
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                (root / name).write_text("# Product")
                resolver = ContextResolver(root)
                path = resolver.resolve_product_path()
                assert path is not None
                assert path.name == name

    def test_discover_design_default_name(self):
        """Test discovery of DESIGN.md in project root."""
        (self.project_root / "DESIGN.md").write_text("# Design")
        path = self.resolver.resolve_design_path()
        assert path is not None
        assert path.name == "DESIGN.md"

    def test_no_files_found(self):
        """Test when no context files exist."""
        product_path = self.resolver.resolve_product_path()
        design_path = self.resolver.resolve_design_path()
        assert product_path is None
        assert design_path is None

    def test_explicit_config_product(self):
        """Test explicit product path in config file."""
        (self.project_root / "custom" / "product.md").parent.mkdir(parents=True)
        (self.project_root / "custom" / "product.md").write_text("# Custom Product")
        
        config_path = self.project_root / "context.json"
        config_data = {"contextFiles": {"product": "custom/product.md"}}
        config_path.write_text(json.dumps(config_data))
        
        path = self.resolver.resolve_product_path()
        assert path is not None
        assert path.name == "product.md"
        assert "custom" in str(path)

    def test_explicit_config_design(self):
        """Test explicit design path in config file."""
        (self.project_root / "brand" / "design.md").parent.mkdir(parents=True)
        (self.project_root / "brand" / "design.md").write_text("# Custom Design")
        
        config_path = self.project_root / "context.json"
        config_data = {"contextFiles": {"design": "brand/design.md"}}
        config_path.write_text(json.dumps(config_data))
        
        path = self.resolver.resolve_design_path()
        assert path is not None
        assert path.name == "design.md"
        assert "brand" in str(path)

    def test_config_in_impeccable_dir(self):
        """Test config file in .impeccable directory."""
        (self.project_root / ".impeccable").mkdir()
        (self.project_root / "governance" / "context" / "product.md").parent.mkdir(parents=True)
        (self.project_root / "governance" / "context" / "product.md").write_text("# Governance Product")
        
        config_path = self.project_root / ".impeccable" / "context.json"
        config_data = {"contextFiles": {"product": "governance/context/product.md"}}
        config_path.write_text(json.dumps(config_data))
        
        path = self.resolver.resolve_product_path()
        assert path is not None
        assert "governance/context" in str(path)

    def test_env_var_product_path(self):
        """Test product path from environment variable."""
        (self.project_root / "env" / "product.md").parent.mkdir(parents=True)
        (self.project_root / "env" / "product.md").write_text("# Env Product")
        
        os.environ["IMPECCABLE_PRODUCT_PATH"] = "env/product.md"
        try:
            resolver = ContextResolver(self.project_root)
            path = resolver.resolve_product_path()
            assert path is not None
            assert "env" in str(path)
        finally:
            del os.environ["IMPECCABLE_PRODUCT_PATH"]

    def test_env_var_design_path(self):
        """Test design path from environment variable."""
        (self.project_root / "env" / "design.md").parent.mkdir(parents=True)
        (self.project_root / "env" / "design.md").write_text("# Env Design")
        
        os.environ["IMPECCABLE_DESIGN_PATH"] = "env/design.md"
        try:
            resolver = ContextResolver(self.project_root)
            path = resolver.resolve_design_path()
            assert path is not None
            assert "env" in str(path)
        finally:
            del os.environ["IMPECCABLE_DESIGN_PATH"]

    def test_config_precedence_over_env(self):
        """Test config file takes precedence over environment variables."""
        (self.project_root / "config" / "product.md").parent.mkdir(parents=True)
        (self.project_root / "config" / "product.md").write_text("# Config Product")
        (self.project_root / "env" / "product.md").parent.mkdir(parents=True)
        (self.project_root / "env" / "product.md").write_text("# Env Product")
        
        config_path = self.project_root / "context.json"
        config_data = {"contextFiles": {"product": "config/product.md"}}
        config_path.write_text(json.dumps(config_data))
        
        os.environ["IMPECCABLE_PRODUCT_PATH"] = "env/product.md"
        try:
            resolver = ContextResolver(self.project_root)
            path = resolver.resolve_product_path()
            assert path is not None
            assert "config" in str(path)
            assert "env" not in str(path)
        finally:
            del os.environ["IMPECCABLE_PRODUCT_PATH"]

    def test_invalid_config_path_outside_project(self):
        """Test that paths outside project root are rejected."""
        outside_dir = self.temp_dir / "outside"
        outside_dir.mkdir()
        (outside_dir / "product.md").write_text("# Outside Product")
        
        config_path = self.project_root / "context.json"
        config_data = {"contextFiles": {"product": "../outside/product.md"}}
        config_path.write_text(json.dumps(config_data))
        
        with pytest.raises(ValueError, match="outside project root"):
            self.resolver.resolve_product_path()

    def test_invalid_config_path_nonexistent(self):
        """Test that nonexistent configured paths raise error."""
        config_path = self.project_root / "context.json"
        config_data = {"contextFiles": {"product": "nonexistent/product.md"}}
        config_path.write_text(json.dumps(config_data))
        
        with pytest.raises(ValueError, match="invalid or outside"):
            self.resolver.resolve_product_path()

    def test_resolve_all(self):
        """Test resolving both paths at once."""
        (self.project_root / "PRODUCT.md").write_text("# Product")
        (self.project_root / "DESIGN.md").write_text("# Design")
        
        resolved = self.resolver.resolve_all()
        assert resolved.product is not None
        assert resolved.design is not None
        assert resolved.product.name == "PRODUCT.md"
        assert resolved.design.name == "DESIGN.md"

    def test_validate_paths_success(self):
        """Test validation with valid paths."""
        (self.project_root / "PRODUCT.md").write_text("# Product")
        (self.project_root / "DESIGN.md").write_text("# Design")
        
        result = self.resolver.validate_paths()
        assert result["valid"] is True
        assert len(result["errors"]) == 0
        assert result["paths"]["product"] is not None
        assert result["paths"]["design"] is not None

    def test_validate_paths_missing_files(self):
        """Test validation when files are missing."""
        result = self.resolver.validate_paths()
        assert result["valid"] is True  # Missing files are warnings, not errors
        assert len(result["warnings"]) == 2
        assert "PRODUCT.md not found" in result["warnings"][0]
        assert "DESIGN.md not found" in result["warnings"][1]

    def test_validate_paths_invalid_config(self):
        """Test validation with invalid configured path."""
        config_path = self.project_root / "context.json"
        config_data = {"contextFiles": {"product": "nonexistent/product.md"}}
        config_path.write_text(json.dumps(config_data))
        
        result = self.resolver.validate_paths()
        assert result["valid"] is False
        assert len(result["errors"]) == 1
        assert "Product path" in result["errors"][0]


class TestCreateDefaultConfig:
    """Tests for create_default_config function."""

    def setup_method(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.project_root = self.temp_dir / "project"
        self.project_root.mkdir()

    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_default_config(self):
        """Test creating default config file."""
        config_path = create_default_config(self.project_root)
        assert config_path.exists()
        assert config_path.name == "context.json"
        
        with open(config_path) as f:
            data = json.load(f)
        assert data["contextFiles"]["product"] is None
        assert data["contextFiles"]["design"] is None

    def test_create_config_with_paths(self):
        """Test creating config with explicit paths."""
        config_path = create_default_config(
            self.project_root,
            product_path="governance/product.md",
            design_path="docs/design.md",
        )
        with open(config_path) as f:
            data = json.load(f)
        assert data["contextFiles"]["product"] == "governance/product.md"
        assert data["contextFiles"]["design"] == "docs/design.md"


class TestDesignSidecar:
    """Tests for DesignSidecar dataclass."""

    def test_default_sidecar(self):
        sidecar = DesignSidecar()
        assert sidecar.schema_version == 2
        assert sidecar.design_fingerprint is None
        assert sidecar.generated_at is None

    def test_sidecar_with_data(self):
        sidecar = DesignSidecar(
            schema_version=2,
            design_fingerprint="abc123",
            generated_at="2024-01-01T00:00:00Z",
        )
        assert sidecar.design_fingerprint == "abc123"
        assert sidecar.generated_at == "2024-01-01T00:00:00Z"

    def test_to_dict(self):
        sidecar = DesignSidecar(
            schema_version=2,
            design_fingerprint="abc123",
            generated_at="2024-01-01T00:00:00Z",
        )
        data = sidecar.to_dict()
        assert data == {
            "schemaVersion": 2,
            "designFingerprint": "abc123",
            "generatedAt": "2024-01-01T00:00:00Z",
        }

    def test_from_dict(self):
        data = {
            "schemaVersion": 2,
            "designFingerprint": "abc123",
            "generatedAt": "2024-01-01T00:00:00Z",
        }
        sidecar = DesignSidecar.from_dict(data)
        assert sidecar.schema_version == 2
        assert sidecar.design_fingerprint == "abc123"
        assert sidecar.generated_at == "2024-01-01T00:00:00Z"

    def test_from_dict_legacy(self):
        """Test loading legacy sidecar without fingerprint."""
        data = {"schemaVersion": 1}
        sidecar = DesignSidecar.from_dict(data)
        assert sidecar.schema_version == 1
        assert sidecar.design_fingerprint is None
        assert sidecar.generated_at is None


class TestStalenessResult:
    """Tests for StalenessResult class."""

    def test_stale_result(self):
        result = StalenessResult(
            stale=True,
            reason="Content changed",
            has_fingerprint=True,
            current_fingerprint="new",
            stored_fingerprint="old",
        )
        assert result.stale is True
        assert result.reason == "Content changed"
        assert result.has_fingerprint is True

    def test_not_stale_result(self):
        result = StalenessResult(
            stale=False,
            reason="Fingerprints match",
            has_fingerprint=True,
            current_fingerprint="same",
            stored_fingerprint="same",
        )
        assert result.stale is False

    def test_to_dict(self):
        result = StalenessResult(
            stale=True,
            reason="Content changed",
            has_fingerprint=True,
            current_fingerprint="new",
            stored_fingerprint="old",
        )
        data = result.to_dict()
        assert data["stale"] is True
        assert data["reason"] == "Content changed"
        assert data["has_fingerprint"] is True
        assert data["current_fingerprint"] == "new"
        assert data["stored_fingerprint"] == "old"


class TestStalenessFingerprint:
    """Tests for staleness detection with SHA-256 fingerprints."""

    def setup_method(self):
        """Create a temporary directory for each test."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.project_root = self.temp_dir / "project"
        self.project_root.mkdir()
        self.resolver = ContextResolver(self.project_root)

    def teardown_method(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_compute_fingerprint(self):
        """Test SHA-256 fingerprint computation."""
        design_path = self.project_root / "DESIGN.md"
        design_path.write_text("# Design\n\nContent here.")
        
        fingerprint = self.resolver.compute_fingerprint(design_path)
        assert len(fingerprint) == 64  # SHA-256 hex digest
        assert all(c in "0123456789abcdef" for c in fingerprint)

    def test_compute_fingerprint_normalizes_line_endings(self):
        """Test that line endings are normalized to LF."""
        design_path = self.project_root / "DESIGN.md"
        # Write with CRLF
        design_path.write_bytes(b"# Design\r\n\r\nContent\r\nhere.")
        
        fingerprint_lf = self.resolver.compute_fingerprint(design_path)
        
        # Write same content with LF
        design_path.write_bytes(b"# Design\n\nContent\nhere.")
        
        fingerprint_crlf = self.resolver.compute_fingerprint(design_path)
        
        assert fingerprint_lf == fingerprint_crlf

    def test_compute_fingerprint_different_content(self):
        """Test that different content produces different fingerprints."""
        design_path1 = self.project_root / "DESIGN1.md"
        design_path2 = self.project_root / "DESIGN2.md"
        design_path1.write_text("# Design\n\nContent A.")
        design_path2.write_text("# Design\n\nContent B.")
        
        fp1 = self.resolver.compute_fingerprint(design_path1)
        fp2 = self.resolver.compute_fingerprint(design_path2)
        
        assert fp1 != fp2

    def test_save_and_load_sidecar(self):
        """Test saving and loading sidecar with fingerprint."""
        design_path = self.project_root / "DESIGN.md"
        design_path.write_text("# Design\n\nOriginal content.")
        
        sidecar = self.resolver.save_sidecar(design_path)
        
        assert sidecar.design_fingerprint is not None
        assert len(sidecar.design_fingerprint) == 64
        assert sidecar.generated_at is not None
        
        # Load and verify
        loaded = self.resolver.load_sidecar()
        assert loaded is not None
        assert loaded.design_fingerprint == sidecar.design_fingerprint
        assert loaded.generated_at == sidecar.generated_at
        assert loaded.schema_version == 2

    def test_check_staleness_no_design_file(self):
        """Test staleness check when DESIGN.md doesn't exist."""
        result = self.resolver.check_design_staleness()
        assert result.stale is False
        assert result.reason == "DESIGN.md not found"
        assert result.has_fingerprint is False

    def test_check_staleness_no_sidecar(self):
        """Test staleness check when sidecar doesn't exist."""
        design_path = self.project_root / "DESIGN.md"
        design_path.write_text("# Design")
        
        result = self.resolver.check_design_staleness(design_path)
        assert result.stale is False
        assert result.reason == "No sidecar found"
        assert result.has_fingerprint is False

    def test_check_staleness_legacy_sidecar_no_fingerprint(self):
        """Test staleness check with legacy sidecar (no fingerprint) -> unverified, not stale."""
        design_path = self.project_root / "DESIGN.md"
        design_path.write_text("# Design\n\nContent.")
        
        # Create legacy sidecar without fingerprint
        sidecar_path = self.project_root / ".impeccable" / "design.json"
        sidecar_path.parent.mkdir(parents=True)
        sidecar_path.write_text(json.dumps({"schemaVersion": 1}))
        
        result = self.resolver.check_design_staleness(design_path, sidecar_path)
        assert result.stale is False
        assert result.has_fingerprint is False
        assert "unverified" in result.reason.lower()
        assert result.current_fingerprint is not None
        assert result.stored_fingerprint is None

    def test_check_staleness_matching_fingerprints(self):
        """Test staleness check when fingerprints match (not stale)."""
        design_path = self.project_root / "DESIGN.md"
        design_path.write_text("# Design\n\nStable content.")
        
        # Save sidecar with fingerprint
        self.resolver.save_sidecar(design_path)
        
        # Check staleness - should not be stale
        result = self.resolver.check_design_staleness(design_path)
        assert result.stale is False
        assert result.reason == "Fingerprints match"
        assert result.has_fingerprint is True
        assert result.current_fingerprint == result.stored_fingerprint

    def test_check_staleness_changed_content(self):
        """Test staleness check when DESIGN.md content changed (stale)."""
        design_path = self.project_root / "DESIGN.md"
        design_path.write_text("# Design\n\nOriginal content.")
        
        # Save sidecar
        self.resolver.save_sidecar(design_path)
        
        # Modify DESIGN.md content
        design_path.write_text("# Design\n\nModified content.")
        
        # Check staleness - should be stale
        result = self.resolver.check_design_staleness(design_path)
        assert result.stale is True
        assert "changed" in result.reason.lower()
        assert result.has_fingerprint is True
        assert result.current_fingerprint != result.stored_fingerprint

    def test_check_staleness_checkout_scenario(self):
        """Test staleness check simulates checkout/worktree: same content, newer mtime."""
        design_path = self.project_root / "DESIGN.md"
        design_path.write_text("# Design\n\nContent for checkout test.")
        
        # Save sidecar (simulates generation)
        self.resolver.save_sidecar(design_path)
        
        # Simulate checkout: touch DESIGN.md to give it newer mtime
        # but KEEP the same content
        import time
        time.sleep(0.01)  # Ensure mtime changes
        design_path.write_text("# Design\n\nContent for checkout test.")  # Same content
        
        # Check staleness - should NOT be stale (content unchanged)
        result = self.resolver.check_design_staleness(design_path)
        assert result.stale is False
        assert result.reason == "Fingerprints match"
        assert result.has_fingerprint is True

    def test_check_staleness_restored_content(self):
        """Test staleness check when content is restored to original."""
        design_path = self.project_root / "DESIGN.md"
        design_path.write_text("# Design\n\nOriginal content.")
        
        # Save sidecar
        self.resolver.save_sidecar(design_path)
        
        # Modify content
        design_path.write_text("# Design\n\nModified content.")
        
        # Verify it's stale
        result = self.resolver.check_design_staleness(design_path)
        assert result.stale is True
        
        # Restore original content
        design_path.write_text("# Design\n\nOriginal content.")
        
        # Check again - should not be stale
        result = self.resolver.check_design_staleness(design_path)
        assert result.stale is False
        assert result.reason == "Fingerprints match"

    def test_check_staleness_malformed_sidecar(self):
        """Test staleness check with malformed sidecar JSON."""
        design_path = self.project_root / "DESIGN.md"
        design_path.write_text("# Design")
        
        # Create malformed sidecar
        sidecar_path = self.project_root / ".impeccable" / "design.json"
        sidecar_path.parent.mkdir(parents=True)
        sidecar_path.write_text("not valid json")
        
        result = self.resolver.check_design_staleness(design_path, sidecar_path)
        assert result.stale is False
        assert result.reason == "No sidecar found"

    def test_sidecar_custom_path(self):
        """Test sidecar operations with custom path."""
        design_path = self.project_root / "DESIGN.md"
        design_path.write_text("# Design")
        
        custom_sidecar = self.project_root / "custom" / "design.json"
        custom_sidecar.parent.mkdir(parents=True)
        
        # Save to custom path
        sidecar = self.resolver.save_sidecar(design_path, custom_sidecar)
        
        # Load from custom path
        loaded = self.resolver.load_sidecar(custom_sidecar)
        assert loaded is not None
        assert loaded.design_fingerprint == sidecar.design_fingerprint
        
        # Check staleness with custom path
        result = self.resolver.check_design_staleness(design_path, custom_sidecar)
        assert result.stale is False
