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
