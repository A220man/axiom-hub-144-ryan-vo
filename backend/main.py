from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
from typing import Optional
from context_resolver import ContextResolver, ContextFilesConfig, create_default_config, DesignSidecar, StalenessResult
from gitignore_manager import (
    GitignoreManager,
    IgnoreCategory,
    CleanResult,
    create_gitignore_manager,
)


class ContextConfigRequest(BaseModel):
    product: str | None = None
    design: str | None = None


class GitignoreInitRequest(BaseModel):
    categories: list[str] | None = None
    auto_add: bool = False


class GitignoreCleanRequest(BaseModel):
    categories: list[str] | None = None
    dry_run: bool = False
    include_worktrees: bool = False


class ContextValidationResponse(BaseModel):
    valid: bool
    errors: list[str]
    warnings: list[str]
    paths: dict[str, str | None]



app = FastAPI(title="Axiom Hub", description="The design language that makes your AI harness better at design")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path.cwd()


def get_resolver() -> ContextResolver:
    """Get a context resolver for the current project."""
    return ContextResolver(get_project_root())


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "axiom-hub"}


@app.get("/api/version")
async def version():
    return {"version": "0.1.0", "name": "axiom-hub-144-ryan-vo"}


@app.get("/api/context/resolve")
async def resolve_context():
    """Resolve PRODUCT.md and DESIGN.md paths."""
    resolver = get_resolver()
    resolved = resolver.resolve_all()
    return resolved.to_dict()


@app.get("/api/context/validate")
async def validate_context():
    """Validate context configuration and paths."""
    resolver = get_resolver()
    return resolver.validate_paths()


@app.post("/api/context/config")
async def create_context_config(request: ContextConfigRequest):
    """Create a default context.json configuration file."""
    project_root = get_project_root()
    config_path = create_default_config(
        project_root,
        product_path=request.product,
        design_path=request.design,
    )
    return {"config_path": str(config_path), "message": "Context configuration created"}


@app.get("/api/context/config")
async def get_context_config():
    """Get current context configuration."""
    resolver = get_resolver()
    config = resolver.get_config()
    return config.to_dict()


def get_gitignore_manager() -> GitignoreManager:
    """Get a gitignore manager for the current project."""
    return create_gitignore_manager(get_project_root())


@app.get("/api/gitignore/init")
async def gitignore_init():
    """Get .gitignore initialization instructions."""
    manager = get_gitignore_manager()
    return manager.generate_init_instructions()


@app.post("/api/gitignore/init")
async def gitignore_init_add(request: GitignoreInitRequest):
    """Add missing .gitignore entries."""
    manager = get_gitignore_manager()
    categories = None
    if request.categories:
        try:
            categories = [IgnoreCategory(c) for c in request.categories]
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid category: {e}")
    
    added = manager.add_missing_entries(categories)
    return {
        "added": [{"pattern": e.pattern, "description": e.description, "category": e.category.value} for e in added],
        "count": len(added),
    }


@app.get("/api/gitignore/status")
async def gitignore_status():
    """Get .gitignore status."""
    manager = get_gitignore_manager()
    return manager.get_status()


@app.post("/api/gitignore/clean")
async def gitignore_clean(request: GitignoreCleanRequest):
    """Clean generated files matching .gitignore patterns."""
    manager = get_gitignore_manager()
    categories = None
    if request.categories:
        try:
            categories = [IgnoreCategory(c) for c in request.categories]
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid category: {e}")
    
    result = manager.clean_generated_files(
        categories=categories,
        dry_run=request.dry_run,
        include_worktrees=request.include_worktrees,
    )
    return {
        "removed_files": [str(p) for p in result.removed_files],
        "removed_dirs": [str(p) for p in result.removed_dirs],
        "errors": result.errors,
        "bytes_freed": result.bytes_freed,
        "dry_run": request.dry_run,
    }
