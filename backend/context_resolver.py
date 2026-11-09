"""
Context Resolver Module

Provides configurable resolution of PRODUCT.md and DESIGN.md paths
across Context, Live Mode, and design tooling.

Also provides staleness detection for DESIGN.md sidecars using
SHA-256 content fingerprints instead of mtime comparison.
"""

import os
import json
import hashlib
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


@dataclass
class DesignSidecar:
    """Sidecar metadata for DESIGN.md including content fingerprint."""
    schema_version: int = 2
    design_fingerprint: Optional[str] = None  # SHA-256 of DESIGN.md content
    generated_at: Optional[str] = None  # ISO timestamp when sidecar was generated

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schemaVersion": self.schema_version,
            "designFingerprint": self.design_fingerprint,
            "generatedAt": self.generated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DesignSidecar":
        return cls(
            schema_version=data.get("schemaVersion", 2),
            design_fingerprint=data.get("designFingerprint"),
            generated_at=data.get("generatedAt"),
        )


class StalenessResult:
    """Result of a staleness check for DESIGN.md sidecar."""
    def __init__(
        self,
        stale: bool,
        reason: Optional[str] = None,
        has_fingerprint: bool = False,
        current_fingerprint: Optional[str] = None,
        stored_fingerprint: Optional[str] = None,
    ):
        self.stale = stale
        self.reason = reason
        self.has_fingerprint = has_fingerprint
        self.current_fingerprint = current_fingerprint
        self.stored_fingerprint = stored_fingerprint

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stale": self.stale,
            "reason": self.reason,
            "has_fingerprint": self.has_fingerprint,
            "current_fingerprint": self.current_fingerprint,
            "stored_fingerprint": self.stored_fingerprint,
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
    DEFAULT_SIDECAR_PATH = ".impeccable/design.json"

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

    # --- Staleness detection with SHA-256 fingerprints ---

    @staticmethod
    def compute_fingerprint(file_path: Path) -> str:
        """Compute SHA-256 fingerprint of file content (normalized line endings)."""
        content = file_path.read_bytes()
        # Normalize line endings to LF for consistent fingerprinting across platforms
        normalized = content.replace(b"\r\n", b"\n")
        return hashlib.sha256(normalized).hexdigest()

    def get_sidecar_path(self) -> Path:
        """Get the default sidecar path."""
        return self.project_root / self.DEFAULT_SIDECAR_PATH

    def load_sidecar(self, sidecar_path: Optional[Path] = None) -> Optional[DesignSidecar]:
        """Load design sidecar from file."""
        path = sidecar_path or self.get_sidecar_path()
        if not path.exists():
            return None
        try:
            with open(path, "r") as f:
                data = json.load(f)
            return DesignSidecar.from_dict(data)
        except (json.JSONDecodeError, OSError):
            return None

    def save_sidecar(
        self,
        design_path: Path,
        sidecar_path: Optional[Path] = None,
        generated_at: Optional[str] = None,
    ) -> DesignSidecar:
        """Generate and save sidecar with DESIGN.md fingerprint."""
        fingerprint = self.compute_fingerprint(design_path)
        if generated_at is None:
            from datetime import datetime, timezone
            generated_at = datetime.now(timezone.utc).isoformat()
        
        sidecar = DesignSidecar(
            design_fingerprint=fingerprint,
            generated_at=generated_at,
        )
        
        path = sidecar_path or self.get_sidecar_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(sidecar.to_dict(), f, indent=2)
        
        return sidecar

    def check_design_staleness(
        self,
        design_path: Optional[Path] = None,
        sidecar_path: Optional[Path] = None,
    ) -> StalenessResult:
        """
        Check if DESIGN.md has changed since sidecar was generated.
        
        Uses SHA-256 content fingerprint comparison instead of mtime.
        Legacy sidecars without fingerprints are treated as 'unverified' (not stale).
        """
        design_path = design_path or self.resolve_design_path()
        if not design_path or not design_path.exists():
            return StalenessResult(
                stale=False,
                reason="DESIGN.md not found",
                has_fingerprint=False,
            )
        
        sidecar = self.load_sidecar(sidecar_path)
        if not sidecar:
            return StalenessResult(
                stale=False,
                reason="No sidecar found",
                has_fingerprint=False,
            )
        
        current_fingerprint = self.compute_fingerprint(design_path)
        
        # Legacy sidecar without fingerprint: unverified, not stale
        if not sidecar.design_fingerprint:
            return StalenessResult(
                stale=False,
                reason="Legacy sidecar without fingerprint (unverified)",
                has_fingerprint=False,
                current_fingerprint=current_fingerprint,
                stored_fingerprint=None,
            )
        
        # Compare fingerprints
        if current_fingerprint != sidecar.design_fingerprint:
            return StalenessResult(
                stale=True,
                reason="DESIGN.md content changed since sidecar generation",
                has_fingerprint=True,
                current_fingerprint=current_fingerprint,
                stored_fingerprint=sidecar.design_fingerprint,
            )
        
        return StalenessResult(
            stale=False,
            reason="Fingerprints match",
            has_fingerprint=True,
            current_fingerprint=current_fingerprint,
            stored_fingerprint=sidecar.design_fingerprint,
        )


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
