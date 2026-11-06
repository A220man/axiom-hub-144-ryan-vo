"""
Tests for Gitignore Manager Module
"""

import os
import json
import tempfile
import shutil
from pathlib import Path
import pytest
import subprocess

from gitignore_manager import (
    GitignoreEntry,
    IgnoreCategory,
    CleanResult,
    GitignoreManager,
    create_gitignore_manager,
    DEFAULT_GITIGNORE_ENTRIES,
)


class TestGitignoreEntry:
    """Tests for GitignoreEntry dataclass."""

    def test_default_entry(self):
        entry = GitignoreEntry(
            pattern=".impeccable/",
            description="Impeccable files",
            category=IgnoreCategory.IMPECCABLE_GENERATED,
        )
        assert entry.pattern == ".impeccable/"
        assert entry.description == "Impeccable files"
        assert entry.category == IgnoreCategory.IMPECCABLE_GENERATED
        assert entry.is_generated is False

    def test_entry_with_generated(self):
        entry = GitignoreEntry(
            pattern="build/",
            description="Build output",
            category=IgnoreCategory.BUILD_ARTIFACTS,
            is_generated=True,
        )
        assert entry.is_generated is True


class TestGitignoreManager:
    """Tests for GitignoreManager class."""

    def setup_method(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.project_root = self.temp_dir / "project"
        self.project_root.mkdir()
        self.manager = GitignoreManager(self.project_root)

    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_default_entries(self):
        entries = self.manager.get_default_entries()
        assert len(entries) == len(DEFAULT_GITIGNORE_ENTRIES)
        assert all(isinstance(e, GitignoreEntry) for e in entries)

    def test_entries_by_category(self):
        by_cat = self.manager.get_entries_by_category()
        assert IgnoreCategory.IMPECCABLE_GENERATED in by_cat
        assert IgnoreCategory.BUILD_ARTIFACTS in by_cat
        assert IgnoreCategory.CACHE_FILES in by_cat
        assert IgnoreCategory.TEMP_FILES in by_cat
        assert IgnoreCategory.IDE_FILES in by_cat
        assert IgnoreCategory.OS_FILES in by_cat

    def test_read_empty_gitignore(self):
        lines = self.manager.read_gitignore()
        assert lines == []

    def test_write_and_read_gitignore(self):
        lines = ["# Comment", "*.log", "build/"]
        self.manager.write_gitignore(lines)
        read_lines = self.manager.read_gitignore()
        assert read_lines == lines

    def test_get_missing_entries_empty_gitignore(self):
        missing = self.manager.get_missing_entries()
        assert len(missing) == len(DEFAULT_GITIGNORE_ENTRIES)

    def test_get_missing_entries_partial(self):
        self.manager.write_gitignore([".impeccable/", "build/"])
        missing = self.manager.get_missing_entries()
        patterns = [e.pattern for e in missing]
        assert ".impeccable/" not in patterns
        assert "build/" not in patterns
        assert "dist/" in patterns

    def test_add_missing_entries(self):
        added = self.manager.add_missing_entries()
        assert len(added) == len(DEFAULT_GITIGNORE_ENTRIES)
        
        # Check file was written
        lines = self.manager.read_gitignore()
        assert any("impeccable" in line.lower() for line in lines)
        assert ".impeccable/" in lines
        assert "build/" in lines

    def test_add_missing_entries_idempotent(self):
        self.manager.add_missing_entries()
        added_again = self.manager.add_missing_entries()
        assert len(added_again) == 0

    def test_add_missing_entries_by_category(self):
        added = self.manager.add_missing_entries([IgnoreCategory.IMPECCABLE_GENERATED])
        patterns = [e.pattern for e in added]
        assert ".impeccable/" in patterns
        assert "build/" not in patterns  # Different category

    def test_generate_init_instructions(self):
        instructions = self.manager.generate_init_instructions()
        assert instructions["missing_count"] == len(DEFAULT_GITIGNORE_ENTRIES)
        assert instructions["total_default_count"] == len(DEFAULT_GITIGNORE_ENTRIES)
        assert "categories" in instructions
        assert "impeccable_generated" in instructions["categories"]
        assert "gitignore_path" in instructions
        assert instructions["auto_add_available"] is True

    def test_clean_generated_files_dry_run(self):
        # Create some generated files
        (self.project_root / ".impeccable").mkdir()
        (self.project_root / ".impeccable" / "cache").mkdir(parents=True)
        (self.project_root / ".impeccable" / "design.json").write_text("{}")
        (self.project_root / "build").mkdir()
        (self.project_root / "build" / "output.js").write_text("console.log('test')")
        (self.project_root / "dist").mkdir()
        (self.project_root / "dist" / "bundle.js").write_text("bundle")

        result = self.manager.clean_generated_files(dry_run=True)
        
        assert len(result.removed_files) > 0
        assert len(result.removed_dirs) > 0
        assert result.errors == []
        # Files should still exist after dry run
        assert (self.project_root / ".impeccable" / "design.json").exists()
        assert (self.project_root / "build" / "output.js").exists()

    def test_clean_generated_files_actual(self):
        # Create some generated files
        (self.project_root / ".impeccable").mkdir()
        (self.project_root / ".impeccable" / "cache").mkdir(parents=True)
        (self.project_root / ".impeccable" / "design.json").write_text("{}")
        (self.project_root / "build").mkdir()
        (self.project_root / "build" / "output.js").write_text("console.log('test')")

        result = self.manager.clean_generated_files(dry_run=False)
        
        assert len(result.removed_files) > 0
        assert len(result.removed_dirs) > 0
        assert result.errors == []
        assert result.bytes_freed > 0
        # Files should be gone
        assert not (self.project_root / ".impeccable" / "design.json").exists()
        assert not (self.project_root / "build" / "output.js").exists()

    def test_clean_by_category(self):
        (self.project_root / ".impeccable").mkdir()
        (self.project_root / ".impeccable" / "design.json").write_text("{}")
        (self.project_root / "build").mkdir()
        (self.project_root / "build" / "output.js").write_text("test")

        # Clean only impeccable_generated
        result = self.manager.clean_generated_files(
            categories=[IgnoreCategory.IMPECCABLE_GENERATED],
            dry_run=False,
        )
        
        assert not (self.project_root / ".impeccable" / "design.json").exists()
        assert (self.project_root / "build" / "output.js").exists()

    def test_get_status(self):
        status = self.manager.get_status()
        assert status["gitignore_exists"] is False
        assert status["existing_entries"] == 0
        assert status["missing_entries"] == len(DEFAULT_GITIGNORE_ENTRIES)

    def test_get_status_with_gitignore(self):
        self.manager.write_gitignore([".impeccable/", "build/"])
        status = self.manager.get_status()
        assert status["gitignore_exists"] is True
        assert status["existing_entries"] == 2
        # .impeccable/ covers .impeccable/cache/, .impeccable/design.json, etc.
        # build/ covers build/ but not dist/
        assert status["missing_entries"] == 14


class TestGitignoreManagerWorktrees:
    """Tests for worktree support."""

    def setup_method(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.main_root = self.temp_dir / "main"
        self.main_root.mkdir()
        
        # Initialize git repo
        subprocess.run(["git", "init"], cwd=self.main_root, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=self.main_root, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=self.main_root, capture_output=True)
        (self.main_root / "README.md").write_text("# Test")
        subprocess.run(["git", "add", "README.md"], cwd=self.main_root, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial"], cwd=self.main_root, capture_output=True)

    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_find_worktree_roots(self):
        manager = GitignoreManager(self.main_root)
        worktrees = manager._find_worktree_roots()
        assert worktrees == []  # No worktrees yet

    def test_worktree_cleanup(self):
        # Create a worktree
        wt_root = self.temp_dir / "worktree"
        subprocess.run(["git", "worktree", "add", str(wt_root), "-b", "feature"], 
                       cwd=self.main_root, capture_output=True)
        
        # Create generated files in both
        for root in [self.main_root, wt_root]:
            (root / ".impeccable").mkdir()
            (root / ".impeccable" / "design.json").write_text("{}")
            (root / "build").mkdir()
            (root / "build" / "output.js").write_text("test")
        
        # Clean from main with worktree support
        manager = GitignoreManager(self.main_root)
        result = manager.clean_generated_files(include_worktrees=True, dry_run=False)
        
        # Both should be cleaned
        assert not (self.main_root / ".impeccable" / "design.json").exists()
        assert not (wt_root / ".impeccable" / "design.json").exists()
        assert not (self.main_root / "build" / "output.js").exists()
        assert not (wt_root / "build" / "output.js").exists()


class TestCreateGitignoreManager:
    """Tests for create_gitignore_manager factory."""

    def test_create_manager(self):
        manager = create_gitignore_manager(Path("/tmp/test"))
        assert isinstance(manager, GitignoreManager)
        assert manager.project_root == Path("/tmp/test")
