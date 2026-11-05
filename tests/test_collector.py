import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from xml.sax.saxutils import escape

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "collect_arxiv.py"
SPEC = importlib.util.spec_from_file_location("collector", MODULE)
collector = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(collector)

GROUPS = [
    {"id": "alpha", "authorQueries": ["Linglong Dai"]},
    {"id": "beta", "authorQueries": ["Kaibin Huang"]},
]


def feed(*papers):
    return '<feed xmlns="http://www.w3.org/2005/Atom">' + "".join(
        '<entry><id>http://arxiv.org/abs/' + item.get("id", "2611.00001v1") + '</id>'
        '<title>' + escape(item.get("title", "Near-field wireless communications")) + '</title>'
        '<published>2026-11-01T00:00:00Z</published><updated>2026-11-02T00:00:00Z</updated>'
        + "".join('<author><name>' + escape(name) + '</name></author>' for name in item.get("authors", ["Linglong Dai"]))
        + '<summary>Example abstract</summary></entry>' for item in papers
    ) + '</feed>'


def results(xml):
    return {"alpha": {"xml": xml}, "beta": {"xml": feed()}}


class CollectorTest(unittest.TestCase):
    def test_only_exact_full_author_and_title_topic_pass(self):
        xml = feed(
            {"id": "2611.00001v1", "authors": ["Ling-Long Dai"]},
            {"id": "2611.00002v1", "authors": ["L. Dai"]},
            {"id": "2611.00003v1", "authors": ["Linglong Dais"]},
            {"id": "2611.00004v1", "title": "A new theory of paleontology"},
        )
        cache, status = collector.merge_candidates({}, GROUPS, results(xml), "2026-11-05T00:00:00Z")
        # A hyphen changes tokenization; only explicitly configured full spelling passes.
        self.assertEqual(cache["papers"], [])
        xml = feed({"authors": ["Línglong DAI"]})
        cache, _ = collector.merge_candidates({}, GROUPS, results(xml), "2026-11-05T00:00:00Z")
        self.assertEqual(len(cache["papers"]), 1)
        self.assertEqual(cache["papers"][0]["candidateStatus"], "pending")
        self.assertIn("仍需核实", cache["papers"][0]["matchEvidence"][0]["reason"])

    def test_baseline_no_change_new_paper_and_revision(self):
        cache, status = collector.merge_candidates({}, GROUPS, results(feed({})), "2026-11-05T00:00:00Z")
        self.assertEqual(status["newCandidates"], 0)
        self.assertEqual(cache["papers"][0]["changeType"], "baseline")
        unchanged, status = collector.merge_candidates(cache, GROUPS, results(feed({})), "2026-11-07T00:00:00Z")
        self.assertEqual(status["newCandidates"], 0)
        self.assertEqual(status["revisedCandidates"], 0)
        new, status = collector.merge_candidates(unchanged, GROUPS, results(feed({}, {"id": "2611.00002v1"})), "2026-11-11T00:00:00Z")
        self.assertEqual(status["newCandidates"], 1)
        revised, status = collector.merge_candidates(new, GROUPS, results(feed({"id": "2611.00001v2"})), "2026-11-14T00:00:00Z")
        self.assertEqual(status["newCandidates"], 0)
        self.assertEqual(status["revisedCandidates"], 1)
        first = next(p for p in revised["papers"] if p["id"] == "2611.00001")
        self.assertEqual(first["versions"], [1, 2])
        self.assertEqual(first["changeType"], "revision")

    def test_coauthor_dedup_and_old_version_cannot_regress(self):
        shared = feed({"authors": ["Linglong Dai", "Kaibin Huang"], "id": "2611.00001v3"})
        cache, _ = collector.merge_candidates({}, GROUPS, {"alpha": {"xml": shared}, "beta": {"xml": shared}}, "2026-11-05T00:00:00Z")
        self.assertEqual(len(cache["papers"]), 1)
        self.assertEqual(cache["papers"][0]["groupIds"], ["alpha", "beta"])
        older, _ = collector.merge_candidates(cache, GROUPS, results(feed({"id": "2611.00001v1", "title": "Old wireless title"})), "2026-11-07T00:00:00Z")
        self.assertEqual(older["papers"][0]["version"], 3)
        self.assertNotEqual(older["papers"][0]["title"], "Old wireless title")

    def test_failed_first_group_remains_baseline_until_its_first_success(self):
        cache, status = collector.merge_candidates({}, GROUPS, {"alpha": {"error": "timeout"}, "beta": {"xml": feed()}}, "2026-11-05T00:00:00Z")
        self.assertEqual(status["state"], "partial")
        cache, status = collector.merge_candidates(cache, GROUPS, results(feed({})), "2026-11-07T00:00:00Z")
        self.assertEqual(status["newCandidates"], 0)
        self.assertEqual(cache["papers"][0]["changeType"], "baseline")

    def test_failure_keeps_cache_bytes_and_editorial_log(self):
        with tempfile.TemporaryDirectory() as temp:
            data = Path(temp)
            collector.write_json(data / "groups.json", GROUPS)
            fixture = data / "fixture.json"
            collector.write_json(fixture, {"now": "2026-11-05T00:00:00Z", "results": results(feed({}))})
            collector.run(data, fixture)
            cache_before = (data / "papers.json").read_bytes()
            (data / "updates.json").write_text('{"updates":[{"type":"baseline"}]}\n', encoding="utf-8")
            log_before = (data / "updates.json").read_bytes()
            collector.write_json(fixture, {"now": "2026-11-07T00:00:00Z", "results": {"alpha": {"error": "timeout"}, "beta": {"xml": "not XML"}}})
            status = collector.run(data, fixture)
            self.assertEqual(status["state"], "error")
            self.assertEqual(status["lastSuccessAt"], "2026-11-05T00:00:00Z")
            self.assertEqual((data / "papers.json").read_bytes(), cache_before)
            self.assertEqual((data / "updates.json").read_bytes(), log_before)

    def test_error_feed_is_failure_not_empty_success(self):
        with self.assertRaises(ValueError):
            collector.parse_feed('<feed xmlns="http://www.w3.org/2005/Atom"><entry><id>http://arxiv.org/api/errors#incorrect_id_format</id></entry></feed>')

    def test_review_is_preserved_for_same_version_and_archived_on_revision(self):
        cache, _ = collector.merge_candidates({}, GROUPS, results(feed({})), "2026-11-05T00:00:00Z")
        cache["papers"][0].update({"candidateStatus": "verified", "reviewedAt": "2026-11-05", "reviewNote": "Checked author affiliation"})
        same, _ = collector.merge_candidates(cache, GROUPS, results(feed({})), "2026-11-07T00:00:00Z")
        self.assertEqual(same["papers"][0]["candidateStatus"], "verified")
        self.assertEqual(same["papers"][0]["reviewedAt"], "2026-11-05")
        revised, _ = collector.merge_candidates(same, GROUPS, results(feed({"id": "2611.00001v2"})), "2026-11-11T00:00:00Z")
        paper = revised["papers"][0]
        self.assertEqual(paper["candidateStatus"], "pending")
        self.assertNotIn("reviewedAt", paper)
        self.assertNotIn("reviewNote", paper)
        self.assertEqual(paper["previousReview"]["version"], 1)
        self.assertEqual(paper["previousReview"]["reviewedAt"], "2026-11-05")

    def test_window_limit_is_explicitly_partial_and_total_is_exposed(self):
        batch = results(feed({}))
        batch["alpha"].update({"cutoff": "2026-10-01T00:00:00Z", "totalResults": 1000, "coverageWarning": "limit reached"})
        _, status = collector.merge_candidates({}, GROUPS, batch, "2026-11-05T00:00:00Z")
        self.assertEqual(status["state"], "partial")
        check = status["groups"][0]
        self.assertEqual(check["sourceTotalResults"], 1000)
        self.assertTrue(check["historicalResultsTruncated"])
        self.assertFalse(check["windowComplete"])


if __name__ == "__main__":
    unittest.main()
