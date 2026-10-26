# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

core-skeleton

## Roadmap

### core-skeleton — Core FastAPI/React skeleton with install instructions and tests

Status: done

Acceptance:
- FastAPI backend runs and serves API
- React frontend builds and loads
- Install instructions in README
- Basic test suite passes

Implementation: `backend/main.py`, `backend/requirements.txt`, `backend/test_main.py`, `frontend/package.json`, `frontend/public/index.html`, `frontend/src/index.js`, `frontend/src/App.js`, `frontend/src/App.css`, `frontend/setupProxy.js`, `README.md`, `PLAN.md`, `STATUS.md`, `CHANGELOG.md`

Tests: `backend/test_main.py`

### context-resolver — Configurable PRODUCT.md and DESIGN.md paths across Context, Live Mode, and design tooling

Status: planned

Acceptance:
- Independent per-document path configuration
- Shared resolution across context, live, and design commands
- Path validation with clear errors
- Backward compatibility with discovery conventions

### gitignore-cleanup — Guidance on .gitignore during init and cleanup command

Status: planned

Acceptance:
- .gitignore instructions during init
- Clean command removes stale generated files
- Works with worktrees

### staleness-fingerprint — SHA-256 fingerprint for DESIGN.md sidecar staleness detection

Status: planned

Acceptance:
- Fingerprint recorded during generation/review
- Content-based comparison instead of mtime
- Legacy sidecars handled gracefully
- Tests for checkout/worktree scenarios

### engine-binary-verification — Independent integrity verification for engine binary downloads

Status: planned

Acceptance:
- Ed25519 signature verification for engine binary
- Re-verification of cached binaries
- Configurable download source with verification
- Release tag synchronization

### rtl-audit — Audit: flag physical CSS properties on RTL pages

Status: planned

Acceptance:
- Sixth Internationalization audit section
- Flags physical properties on RTL pages
- Informational on LTR pages
- Score rescaling from /20 to /24

### background-cascade-fix — Static cascade: reset background-color for image-only shorthands

Status: planned

Acceptance:
- Color reset for background shorthand with image but no color
- Hover pass handles reset correctly
- Gradient shorthands handled
- Golden tests updated

### vue-preview-accept — Vue preview mode: Svelte-parity accept path

Status: planned

Acceptance:
- Param values threaded through Vue accept
- CSS sanitization for Vue (scoped, dedupe, param baking)
- Fixtures for non-happy style-block shapes
- Variant zero validation

### extension-copy-issues — Browser extension: copy all detected issues

Status: planned

Acceptance:
- Copy all issues action in popup
- Markdown output with URL, count, issues, selectors, guidance
- Copy confirmation

