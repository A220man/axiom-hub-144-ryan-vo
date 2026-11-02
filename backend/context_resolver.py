"""
Context Resolver Module

Provides configurable resolution of PRODUCT.md and DESIGN.md paths
across Context, Live Mode, and design tooling.
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field


@dataclass
class ContextFilesConfig:
    """Configuration for context document paths."""
    product: Optional[str] = None
    design: Optional[str] = None

    def to_dict(self) -> Dict[str, Optional[str]]:
        return {"product": self.product, "design": self.design}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContextFilesConfig":
        return cls(
            product=data.get("product"),
            design=data.get("design"),
        )


@dataclass
class ResolvedPaths:
    """Resolved absolute paths for context documents."""
    product: Optional[Path] = None
    design: Optional[Path] = None
    config_path: Optional[Path] = None

    def to_dict(self) -> Dict[str, Optional[str]]:
        return {
            "product": str(self.product) if self.product else None,
            "design": str(self.design) if self.design else None,
            "config_path": str(self.config_path) if self.config_path else None,
        }


class ContextResolver:
    """
    Resolves PRODUCT.md and DESIGN.md paths from configuration or discovery.
    
    Configuration precedence:
    1. Explicit config file (context.json or .impeccable/context.json)
    2. Environment variables (IMPECCABLE_PRODUCT_PATH, IMPECCABLE_DESIGN_PATH)
    3. Default discovery (PRODUCT.md, DESIGN.md in project root)
    """

    DEFAULT_CONFIG_NAMES = ["context.json", ".impeccable/context.json"]
    DEFAULT_PRODUCT_NAMES = ["PRODUCT.md", "product.md", "Product.md"]
    DEFAULT_DESIGN_NAMES = ["DESIGN.md", "design.md", "Design.md"]

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self._config: Optional[ContextFilesConfig] = None
        self._config_path: Optional[Path] = None

    def load_config(self, config_path: Optional[Path] = None) -> ContextFilesConfig:
        """Load context configuration from file."""
        if config_path:
            paths = [config_path]
        else:
            paths = [self.project_root / name for name in self.DEFAULT_CONFIG_NAMES]

        for path in paths:
            if path.exists() and path.is_file():
                try:
                    with open(path, "r") as f:
                        data = json.load(f)
                    context_files = data.get("contextFiles", {})
                    self._config = ContextFilesConfig.from_dict(context_files)
                    self._config_path = path
                    return self._config
                except (json.JSONDecodeError, OSError):
                    continue

        # Check environment variables
        env_config = ContextFilesConfig(
            product=os.environ.get("IMPECCABLE_PRODUCT_PATH"),
            design=os.environ.get("IMPECCABLE_DESIGN_PATH"),
        )
        if env_config.product or env_config.design:
            self._config = env_config
            return self._config

        self._config = ContextFilesConfig()
        return self._config

    def get_config(self) -> ContextFilesConfig:
        """Get current config, loading if necessary."""
        if self._config is None:
            return self.load_config()
        return self._config

    def resolve_product_path(self) -> Optional[Path]:
        """Resolve the PRODUCT.md path."""
        config = self.get_config()
        
        # 1. Explicit config path
        if config.product:
            path = self._resolve_relative_path(config.product)
            if path and self._is_within_project(path):
                return path
            raise ValueError(f"Configured product path '{config.product}' is invalid or outside project root")

        # 2. Default discovery
        return self._discover_file(self.DEFAULT_PRODUCT_NAMES)

    def resolve_design_path(self) -> Optional[Path]:
        """Resolve the DESIGN.md path."""
        config = self.get_config()
        
        # 1. Explicit config path
        if config.design:
            path = self._resolve_relative_path(config.design)
            if path and self._is_within_project(path):
                return path
            raise ValueError(f"Configured design path '{config.design}' is invalid or outside project root")

        # 2. Default discovery
        return self._discover_file(self.DEFAULT_DESIGN_NAMES)

    def resolve_all(self) -> ResolvedPaths:
        """Resolve both product and design paths."""
        return ResolvedPaths(
            product=self.resolve_product_path(),
            design=self.resolve_design_path(),
            config_path=self._config_path,
        )

    def _resolve_relative_path(self, rel_path: str) -> Optional[Path]:
        """Resolve a relative path against project root."""
        path = Path(rel_path)
        if path.is_absolute():
            return path if path.exists() else None
        full_path = (self.project_root / path).resolve()
        return full_path if full_path.exists() else None

    def _discover_file(self, names: list[str]) -> Optional[Path]:
        """Discover a file by trying multiple names in project root."""
        for name in names:
            path = self.project_root / name
            if path.exists() and path.is_file():
                return path
        return None

    def _is_within_project(self, path: Path) -> bool:
        """Check if path is within project root (prevents traversal)."""
        try:
            path.resolve().relative_to(self.project_root.resolve())
            return True
        except ValueError:
            return False

    def validate_paths(self) -> Dict[str, Any]:
        """Validate resolved paths and return status."""
        result = {"valid": True, "errors": [], "warnings": [], "paths": {}}
        
        try:
            product_path = self.resolve_product_path()
            result["paths"]["product"] = str(product_path) if product_path else None
            if not product_path:
                result["warnings"].append("PRODUCT.md not found (configured or discovered)")
        except ValueError as e:
            result["valid"] = False
            result["errors"].append(f"Product path: {e}")

        try:
            design_path = self.resolve_design_path()
            result["paths"]["design"] = str(design_path) if design_path else None
            if not design_path:
                result["warnings"].append("DESIGN.md not found (configured or discovered)")
        except ValueError as e:
            result["valid"] = False
            result["errors"].append(f"Design path: {e}")

        return result


def create_default_config(project_root: Path, product_path: Optional[str] = None, design_path: Optional[str] = None) -> Path:
    """Create a default context.json configuration file."""
    config_data = {
        "contextFiles": {
            "product": product_path,
            "design": design_path,
        }
    }
    config_path = project_root / "context.json"
    with open(config_path, "w") as f:
        json.dump(config_data, f, indent=2)
    return config_path
