"""Rerun recovery must combine complete families from different attempts."""

from pathlib import Path
import tempfile
import unittest

from merge_unified_family_artifacts import merge


class UnifiedArtifactMergeTest(unittest.TestCase):
    def test_latest_complete_family_wins_and_other_families_continue(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            artifacts = root / "artifacts"
            artifacts.mkdir()

            def artifact(attempt, family, *, complete):
                folder = artifacts / f"unified-family-123-{attempt}-{family}" / "unified" / family
                folder.mkdir(parents=True)
                (folder / "value.txt").write_text(f"{family}-{attempt}", encoding="utf-8")
                if complete:
                    (folder / "unified-family-manifest.json").write_text("{}", encoding="utf-8")

            artifact(1, "washer", complete=False)
            artifact(1, "tv", complete=True)
            artifact(2, "washer", complete=True)
            artifact(3, "washer", complete=False)
            selected = merge(artifacts, "123", root / "merged")
            self.assertEqual(selected["washer"], 2)
            self.assertEqual(selected["tv"], 1)
            self.assertEqual((root / "merged/unified/washer/value.txt").read_text(), "washer-2")
            self.assertEqual((root / "merged/unified/tv/value.txt").read_text(), "tv-1")
