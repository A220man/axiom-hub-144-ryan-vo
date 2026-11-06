"""
Gitignore Manager Module

Provides .gitignore guidance during init and cleanup commands
for generated files, with worktree support.
"""

import os
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Set
from dataclasses import dataclass, field
from enum import Enum


class IgnoreCategory(Enum):
    """Categories of files to ignore."""
    IMPECCABLE_GENERATED = "impeccable_generated"
    BUILD_ARTIFACTS = "build_artifacts"
    CACHE_FILES = "cache_files"
    TEMP_FILES = "temp_files"
    IDE_FILES = "ide_files"
    OS_FILES = "os_files"


@dataclass
class GitignoreEntry:
    """A single .gitignore entry with metadata."""
    pattern: str
    description: str
    category: IgnoreCategory
    is_generated: bool = False


@dataclass
class CleanResult:
    """Result of a clean operation."""
    removed_files: List[Path] = field(default_factory=list)
    removed_dirs: List[Path] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    bytes_freed: int = 0


# Default .gitignore entries for impeccable projects
DEFAULT_GITIGNORE_ENTRIES: List[GitignoreEntry] = [
    # Impeccable generated files
    GitignoreEntry(
        pattern=".impeccable/",
        description="Impeccable generated files and cache",
        category=IgnoreCategory.IMPECCABLE_GENERATED,
        is_generated=True,
    ),
    GitignoreEntry(
        pattern=".impeccable/context.json",
        description="Impeccable context configuration",
        category=IgnoreCategory.IMPECCABLE_GENERATED,
        is_generated=True,
    ),
    GitignoreEntry(
        pattern=".impeccable/design.json",
        description="Impeccable design sidecar",
        category=IgnoreCategory.IMPECCABLE_GENERATED,
        is_generated=True,
    ),
    GitignoreEntry(
        pattern=".impeccable/cache/",
        description="Impeccable cache directory",
        category=IgnoreCategory.IMPECCABLE_GENERATED,
        is_generated=True,
    ),
    GitignoreEntry(
        pattern=".impeccable/sessions/",
        description="Impeccable session files",
        category=IgnoreCategory.IMPECCABLE_GENERATED,
        is_generated=True,
    ),
    GitignoreEntry(
        pattern=".impeccable/*.log",
        description="Impeccable log files",
        category=IgnoreCategory.IMPECCABLE_GENERATED,
        is_generated=True,
    ),
    # Build artifacts
    GitignoreEntry(
        pattern="build/",
        description="Build output directory",
        category=IgnoreCategory.BUILD_ARTIFACTS,
        is_generated=True,
    ),
    GitignoreEntry(
        pattern="dist/",
        description="Distribution output directory",
        category=IgnoreCategory.BUILD_ARTIFACTS,
        is_generated=True,
    ),
    # Cache files
    GitignoreEntry(
        pattern="*.pyc",
        description="Python compiled bytecode",
        category=IgnoreCategory.CACHE_FILES,
        is_generated=True,
    ),
    GitignoreEntry(
        pattern="__pycache__/",
        description="Python cache directory",
        category=IgnoreCategory.CACHE_FILES,
        is_generated=True,
    ),
    GitignoreEntry(
        pattern=".pytest_cache/",
        description="Pytest cache directory",
        category=IgnoreCategory.CACHE_FILES,
        is_generated=True,
    ),
    GitignoreEntry(
        pattern="node_modules/",
        description="Node.js dependencies",
        category=IgnoreCategory.CACHE_FILES,
        is_generated=True,
    ),
    # Temp files
    GitignoreEntry(
        pattern="*.tmp",
        description="Temporary files",
        category=IgnoreCategory.TEMP_FILES,
        is_generated=True,
    ),
    GitignoreEntry(
        pattern="*.temp",
        description="Temporary files",
        category=IgnoreCategory.TEMP_FILES,
        is_generated=True,
    ),
    GitignoreEntry(
        pattern="*.bak",
        description="Backup files",
        category=IgnoreCategory.TEMP_FILES,
        is_generated=True,
    ),
    # IDE files
    GitignoreEntry(
        pattern=".vscode/",
        description="VS Code settings",
        category=IgnoreCategory.IDE_FILES,
        is_generated=False,
    ),
    GitignoreEntry(
        pattern=".idea/",
        description="JetBrains IDE settings",
        category=IgnoreCategory.IDE_FILES,
        is_generated=False,
    ),
    GitignoreEntry(
        pattern="*.swp",
        description="Vim swap files",
        category=IgnoreCategory.IDE_FILES,
        is_generated=False,
    ),
    GitignoreEntry(
        pattern="*.swo",
        description="Vim swap files",
        category=IgnoreCategory.IDE_FILES,
        is_generated=False,
    ),
    # OS files
    GitignoreEntry(
        pattern=".DS_Store",
        description="macOS directory metadata",
        category=IgnoreCategory.OS_FILES,
        is_generated=False,
    ),
    GitignoreEntry(
        pattern="Thumbs.db",
        description="Windows thumbnail cache",
        category=IgnoreCategory.OS_FILES,
        is_generated=False,
    ),
]


class GitignoreManager:
    """Manages .gitignore file for the project."""

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.gitignore_path = self.project_root / ".gitignore"

    def get_default_entries(self) -> List[GitignoreEntry]:
        """Get the default .gitignore entries."""
        return DEFAULT_GITIGNORE_ENTRIES

    def get_entries_by_category(self) -> Dict[IgnoreCategory, List[GitignoreEntry]]:
        """Get entries grouped by category."""
        by_category: Dict[IgnoreCategory, List[GitignoreEntry]] = {}
        for entry in DEFAULT_GITIGNORE_ENTRIES:
            by_category.setdefault(entry.category, []).append(entry)
        return by_category

    def read_gitignore(self) -> List[str]:
        """Read existing .gitignore lines."""
        if not self.gitignore_path.exists():
            return []
        with open(self.gitignore_path, "r") as f:
            return [line.rstrip("\n") for line in f]

    def write_gitignore(self, lines: List[str]) -> None:
        """Write lines to .gitignore."""
        with open(self.gitignore_path, "w") as f:
            f.write("\n".join(lines) + "\n")

    def get_missing_entries(self) -> List[GitignoreEntry]:
        """Get default entries that are not in .gitignore."""
        existing = set(self.read_gitignore())
        missing = []
        for entry in DEFAULT_GITIGNORE_ENTRIES:
            if entry.pattern not in existing:
                # Also check if pattern is covered by a broader pattern
                covered = False
                for line in existing:
                    if line.endswith("/") and entry.pattern.startswith(line):
                        covered = True
                        break
                if not covered:
                    missing.append(entry)
        return missing

    def add_missing_entries(self, categories: Optional[List[IgnoreCategory]] = None) -> List[GitignoreEntry]:
        """Add missing default entries to .gitignore."""
        existing_lines = self.read_gitignore()
        missing = self.get_missing_entries()

        if categories:
            missing = [e for e in missing if e.category in categories]

        if not missing:
            return []

        # Add a comment header if file is empty or doesn't have our marker
        has_impeccable_section = any(
            "impeccable" in line.lower() for line in existing_lines
        )

        new_lines = existing_lines[:]
        if not has_impeccable_section:
            if new_lines and new_lines[-1] != "":
                new_lines.append("")
            new_lines.append("# Impeccable generated files and cache")
            new_lines.append("# Added by impeccable init")

        for entry in missing:
            new_lines.append(entry.pattern)

        self.write_gitignore(new_lines)
        return missing

    def generate_init_instructions(self) -> Dict:
        """Generate .gitignore instructions for init."""
        missing = self.get_missing_entries()
        by_category = self.get_entries_by_category()

        return {
            "missing_count": len(missing),
            "total_default_count": len(DEFAULT_GITIGNORE_ENTRIES),
            "categories": {
                cat.value: [
                    {"pattern": e.pattern, "description": e.description}
                    for e in entries
                ]
                for cat, entries in by_category.items()
            },
            "gitignore_path": str(self.gitignore_path),
            "auto_add_available": True,
        }

    def clean_generated_files(
        self,
        categories: Optional[List[IgnoreCategory]] = None,
        dry_run: bool = False,
        include_worktrees: bool = False,
    ) -> CleanResult:
        """Remove generated files matching ignore patterns."""
        result = CleanResult()

        # Get patterns for generated files
        patterns = [
            e.pattern
            for e in DEFAULT_GITIGNORE_ENTRIES
            if e.is_generated and (not categories or e.category in categories)
        ]

        # Find worktree roots if requested
        worktree_roots = [self.project_root]
        if include_worktrees:
            worktree_roots.extend(self._find_worktree_roots())

        for root in worktree_roots:
            for pattern in patterns:
                self._clean_pattern(root, pattern, result, dry_run)

        return result

    def _find_worktree_roots(self) -> List[Path]:
        """Find Git worktree roots."""
        roots = []
        git_dir = self.project_root / ".git"
        if git_dir.is_file():
            # This is a worktree, find the main worktree
            with open(git_dir, "r") as f:
                content = f.read()
                if content.startswith("gitdir: "):
                    main_gitdir = content[8:].strip()
                    main_root = Path(main_gitdir).parent
                    if main_root != self.project_root:
                        roots.append(main_root)
        elif git_dir.is_dir():
            # Check for worktrees in .git/worktrees
            worktrees_dir = git_dir / "worktrees"
            if worktrees_dir.exists():
                for wt_dir in worktrees_dir.iterdir():
                    gitfile = wt_dir / "gitdir"
                    if gitfile.exists():
                        with open(gitfile, "r") as f:
                            wt_gitdir = f.read().strip()
                            wt_root = Path(wt_gitdir).parent
                            if wt_root != self.project_root:
                                roots.append(wt_root)
        return roots

    def _clean_pattern(
        self,
        root: Path,
        pattern: str,
        result: CleanResult,
        dry_run: bool,
    ) -> None:
        """Clean files matching a pattern."""
        # Handle directory patterns (ending with /)
        if pattern.endswith("/"):
            dir_pattern = pattern[:-1]
            for path in root.rglob(dir_pattern):
                if path.is_dir():
                    self._remove_path(path, result, dry_run)
        else:
            # Handle file patterns
            for path in root.rglob(pattern):
                if path.is_file():
                    self._remove_path(path, result, dry_run)
                elif path.is_dir() and not any(path.iterdir()):
                    # Empty directory matching file pattern
                    self._remove_path(path, result, dry_run)

    def _remove_path(self, path: Path, result: CleanResult, dry_run: bool) -> None:
        """Remove a file or directory."""
        try:
            if path.is_file():
                size = path.stat().st_size
                if not dry_run:
                    path.unlink()
                result.removed_files.append(path)
                result.bytes_freed += size
            elif path.is_dir():
                # Count files in directory before removing
                if not dry_run:
                    for file_path in path.rglob("*"):
                        if file_path.is_file():
                            size = file_path.stat().st_size
                            result.removed_files.append(file_path)
                            result.bytes_freed += size
                    shutil.rmtree(path)
                else:
                    # Dry run - count files
                    for file_path in path.rglob("*"):
                        if file_path.is_file():
                            result.removed_files.append(file_path)
                            result.bytes_freed += file_path.stat().st_size
                result.removed_dirs.append(path)
        except Exception as e:
            result.errors.append(f"Failed to remove {path}: {e}")

    def get_status(self) -> Dict:
        """Get gitignore status."""
        missing = self.get_missing_entries()
        existing = self.read_gitignore()

        return {
            "gitignore_exists": self.gitignore_path.exists(),
            "gitignore_path": str(self.gitignore_path),
            "existing_entries": len(existing),
            "missing_entries": len(missing),
            "missing_patterns": [e.pattern for e in missing],
            "worktree_roots": [str(r) for r in self._find_worktree_roots()],
        }


def create_gitignore_manager(project_root: Optional[Path] = None) -> GitignoreManager:
    """Create a GitignoreManager instance."""
    return GitignoreManager(project_root)
