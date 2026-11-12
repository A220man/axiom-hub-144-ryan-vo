# Changelog

## 1.4.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.3.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.3.0 — work-in-progress checkpoint

### Added
- SHA-256 fingerprint for DESIGN.md sidecar staleness detection (staleness-fingerprint)
  - `ContextResolver.compute_fingerprint()` for content-based SHA-256 hashing with line-ending normalization
  - `DesignSidecar` dataclass with schema version, fingerprint, and generation timestamp
  - `StalenessResult` class for detailed staleness check results
  - `save_sidecar()` to generate and persist sidecar with fingerprint
  - `check_design_staleness()` for content-based comparison (replaces mtime-based)
  - Legacy sidecars without fingerprints treated as "unverified" (not stale)
  - Comprehensive test coverage (21 new tests) including checkout/worktree scenarios

## 1.3.0 — work-in-progress checkpoint

### Added
- Gitignore manager for .gitignore guidance during init and cleanup
- New API endpoints: `/api/gitignore/init`, `/api/gitignore/status`, `/api/gitignore/clean`
- Gitignore management UI in frontend with dry-run and worktree support
- Comprehensive test suite for gitignore manager (20 tests)
- Worktree-aware cleanup for generated files

## 1.2.0 — work-in-progress checkpoint

### Added
- Context resolver for configurable PRODUCT.md and DESIGN.md paths
- New API endpoints: `/api/context/resolve`, `/api/context/validate`, `/api/context/config`
- Context resolution display in frontend
- Comprehensive test suite for context resolver (32 tests)

## 1.1.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.0.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.0.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

All notable changes to this project will be documented in this file.

## [0.1.0] - 2026-10-26

### Added
- Initial FastAPI/React skeleton
- Backend health and version endpoints
- Frontend with backend status display
- Basic test suite
- Install documentation
- Feature roadmap (feature-plan.json)
- Implementation plan (PLAN.md)
- Status tracking (STATUS.md)
