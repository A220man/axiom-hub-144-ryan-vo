from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
from context_resolver import ContextResolver, ContextFilesConfig, create_default_config


class ContextConfigRequest(BaseModel):
    product: str | None = None
    design: str | None = None


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
