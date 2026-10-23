"""Synthetic fixtures only: no networking, environment, SMTP or document writes."""
import copy
from datetime import datetime, timezone
import importlib
import unittest

NOW = datetime(2026, 10, 22, 13, 32, tzinfo=timezone.utc)


def article():
    return {
        "story_id": "synthetic-story", "url": "https://example.org/story",
        "source": "Synthetic publisher", "published_at": "2026-10-22T09:00:00+00:00",
        "published_evidence": {"url": "https://example.org/story", "excerpt": "Published 22 October 2026 at 09:00 UTC", "published_at": "2026-10-22T09:00:00+00:00"},
        "event_date": "2027-01-01",
        "fr": {"title": "Titre fictif", "interest": "Intérêt de cette information fictive.", "summary": " ".join(["information"] * 65)},
        "en": {"title": "Synthetic title", "interest": "Why this synthetic story matters.", "summary": " ".join(["report"] * 65)},
        "verification": {"status": "source_consulted", "sources": [{"url": "https://example.org/story", "origin": "Synthetic publisher", "consulted_at": "2026-10-22T10:00:00+00:00", "excerpt": "Synthetic source text actually recorded by a reviewer."}]},
    }


class EditorialTests(unittest.TestCase):
    def api(self):
        self.assertIsNotNone(importlib.util.find_spec("editorial"), "editorial module must exist")
        return importlib.import_module("editorial")

    def test_window_and_published_evidence_are_required(self):
        api = self.api()
        cases = [(article(), True)]
        for value in ("2026-10-21T13:31:59+00:00", "2026-10-22T13:32:01+00:00", "2026-10-22T09:00:00", "2026-10-22", None):
            a = article(); a["published_at"] = value; cases.append((a, False))
        for evidence in ({}, {"url": "https://example.org/story", "excerpt": "today"}):
            a = article(); a["published_evidence"] = evidence; cases.append((a, False))
        for a, valid in cases:
            with self.subTest(a=a):
                result = api.validate_edition({"articles": [a]}, now=NOW)
                self.assertEqual(len(result["articles"]), int(valid))
                self.assertEqual(bool(result["excluded"]), not valid)
        self.assertEqual(result["timezone"], "Africa/Abidjan")

    def test_bilingual_fields_lengths_paths_and_duplicates(self):
        api = self.api()
        for field in ("story_id", "url", "source"):
            a = article(); a[field] = ""
            self.assertEqual(api.validate_edition({"articles": [a]}, now=NOW)["articles"], [])
        for lang in ("fr", "en"):
            for field in ("title", "interest", "summary"):
                a = article(); a[lang][field] = ""
                self.assertEqual(api.validate_edition({"articles": [a]}, now=NOW)["articles"], [])
            for count in (59, 91):
                a = article(); a[lang]["summary"] = " ".join(["word"] * count)
                self.assertEqual(api.validate_edition({"articles": [a]}, now=NOW)["articles"], [])
            for path in ("/Users/person/private", "file:///tmp/draft", "C:\\Users\\person\\draft", "/tmp/draft"):
                a = article(); a[lang]["interest"] = path
                self.assertEqual(api.validate_edition({"articles": [a]}, now=NOW)["articles"], [])
        a = article(); a["en"] = copy.deepcopy(a["fr"])
        self.assertEqual(api.validate_edition({"articles": [a]}, now=NOW)["articles"], [])
        for field in ("url", "story_id"):
            a = article(); b = article(); b["url"] += "2"; b["story_id"] += "2"; b[field] = a[field]
            self.assertEqual(len(api.validate_edition({"articles": [a, b]}, now=NOW)["articles"]), 1)
        a = article(); b = article(); b["story_id"] += "2"; b["url"] += "?utm_source=test#top"
        self.assertEqual(len(api.validate_edition({"articles": [a, b]}, now=NOW)["articles"]), 1)

    def test_verification_requires_consultation_primary_and_independence(self):
        api = self.api()
        for verification in ({}, {"status": "verified", "sources": []}, {"status": "source_consulted", "sources": []}):
            a = article(); a["verification"] = verification
            self.assertFalse(api.validate_edition({"articles": [a]}, now=NOW)["articles"])
        for field in ("origin", "excerpt", "consulted_at", "url"):
            a = article(); del a["verification"]["sources"][0][field]
            self.assertFalse(api.validate_edition({"articles": [a]}, now=NOW)["articles"])
        a = article(); a["verification"]["status"] = "primary"
        self.assertFalse(api.validate_edition({"articles": [a]}, now=NOW)["articles"])
        a["verification"]["sources"][0].update(is_primary=True, primary_evidence="Publisher issued this original statement")
        self.assertEqual(len(api.validate_edition({"articles": [a]}, now=NOW)["articles"]), 1)
        a = article(); a["verification"]["status"] = "corroborated"
        self.assertFalse(api.validate_edition({"articles": [a]}, now=NOW)["articles"])
        b = copy.deepcopy(a["verification"]["sources"][0]); b["url"] = "https://second.example.net/report"
        a["verification"]["sources"].append(b)
        self.assertFalse(api.validate_edition({"articles": [a]}, now=NOW)["articles"])
        b.update(origin="Independent newsroom", independence_evidence="Separately reported, not a syndicated copy")
        a["verification"]["sources"][0]["independence_evidence"] = "Original independent reporting"
        self.assertEqual(len(api.validate_edition({"articles": [a]}, now=NOW)["articles"]), 1)
        b["url"] = "https://example.org/another"
        self.assertFalse(api.validate_edition({"articles": [a]}, now=NOW)["articles"])

    def test_rendered_drafts_mime_and_separate_report(self):
        api = self.api()
        self.assertTrue(hasattr(api, "prepare_draft"), "prepare_draft API required")
        a = article(); a["fr"]["title"] = "Titre <script>alert(1)</script>"
        result = api.prepare_draft({"articles": [a], "limitations": ["Aucune source supplémentaire consultée."]}, now=NOW)
        self.assertIn("lang=\"fr\"", result["html_fr"])
        self.assertIn("lang=\"en\"", result["html_en"])
        self.assertIn("&lt;script&gt;", result["html_fr"])
        self.assertNotIn("<script>", result["html_fr"])
        self.assertIn(a["fr"]["summary"], result["html_fr"])
        self.assertNotIn(a["fr"]["summary"], result["html_en"])
        self.assertIn(a["event_date"], result["html_en"])
        self.assertIn("source", result["html_en"].lower())
        self.assertNotIn("excluded", result["html_fr"])
        self.assertEqual(result["report"]["accepted_count"], 1)
        self.assertFalse(result["report"]["sent"])
        self.assertTrue(result["report"]["human_review_required"])
        from email.parser import BytesParser
        from email.policy import default
        message = BytesParser(policy=default).parsebytes(result["mime_bytes"])
        attachments = list(message.iter_attachments())
        self.assertEqual([p.get_filename() for p in attachments], ["draft_fr.html", "draft_en.html"])
        self.assertEqual([p.get_content_type() for p in attachments], ["text/html", "text/html"])
        self.assertEqual(attachments[0].get_content(), result["html_fr"])
        self.assertNotIn("/Users/", str(message))
        empty = api.prepare_draft({"articles": []}, now=NOW)
        self.assertEqual(empty["report"]["accepted_count"], 0)
        self.assertIn("Aucun article", empty["html_fr"])
        self.assertIn("No eligible", empty["html_en"])
        self.assertTrue(empty["report"]["limitations"])

    def test_reader_body_preserves_limits_and_verification_details(self):
        from email.parser import BytesParser
        from email.policy import default
        a = article()
        a['fr']['verification_note'] = 'Source originale non consultée ; divergence conservée.'
        a['en']['verification_note'] = 'Original source not consulted; discrepancy retained.'
        data = {'articles': [a], 'limitations': ['Diversité des sources insuffisante.']}
        result = self.api().prepare_draft(data, now=NOW)
        for lang in ('fr', 'en'):
            self.assertIn(a[lang]['verification_note'], result['html_' + lang])
            self.assertIn(data['limitations'][0], result['html_' + lang])
        message = BytesParser(policy=default).parsebytes(result['mime_bytes'])
        plain = message.get_body(preferencelist=('plain',)).get_content()
        self.assertIn(a['fr']['summary'], plain)
        self.assertIn(a['en']['summary'], plain)
        self.assertIn(a['en']['verification_note'], plain)

    def test_run_requires_prepared_file_and_never_sends_or_collects(self):
        import inspect
        import news_brief
        from unittest.mock import patch
        import io
        import json
        self.assertIn("editorial_file", inspect.signature(news_brief.run).parameters)
        with patch.object(news_brief, "gather", side_effect=AssertionError("network forbidden")), patch.object(news_brief, "ensure_dirs", side_effect=AssertionError("write forbidden")):
            with self.assertRaisesRegex(ValueError, "editorial"):
                news_brief.run()
            with self.assertRaisesRegex(RuntimeError, "[Hh]uman review|revue humaine"):
                news_brief.run(send_email=True)
            with patch("builtins.open", return_value=io.StringIO(json.dumps({"articles": [article()]}))):
                result = news_brief.run(editorial_file="explicit.json", now=NOW)
            self.assertEqual(result["report"]["accepted_count"], 1)
            self.assertFalse(result["report"]["sent"])
        import warnings
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            legacy = news_brief.curate([{"title": "Unreviewed", "url": "https://example.org/story"}])
        self.assertEqual(legacy[0]["verified"], "unverified")
        self.assertTrue(caught)
        self.assertNotIn("source consultée", news_brief.item_block(legacy[0], "fr"))

    def test_malformed_records_are_excluded_and_review_may_follow_cutoff(self):
        api = self.api()
        for bad in (None, [], "bad", {"fr": []}):
            with self.subTest(bad=bad):
                result = api.validate_edition({"articles": [bad]}, now=NOW)
                self.assertEqual(len(result["excluded"]), 1)
        for field, bad in (("fr", []), ("verification", ["bad"]), ("published_evidence", ["bad"]), ("event_date", "/Users/private/draft")):
            a = article(); a[field] = bad
            self.assertFalse(api.validate_edition({"articles": [a]}, now=NOW)["articles"])
        for data in ({}, {"articles": "bad"}, {"articles": None}, []):
            with self.assertRaises(ValueError):
                api.validate_edition(data, now=NOW)
        a = article(); a["verification"]["sources"][0]["consulted_at"] = "2026-10-22T14:00:00+00:00"
        self.assertEqual(len(api.validate_edition({"articles": [a]}, now=NOW)["articles"]), 1)
        a = article(); a["published_evidence"]["timezone_basis"] = "assumed Africa/Abidjan, publisher does not specify zone"
        result = api.prepare_draft({"articles": [a]}, now=NOW)
        self.assertTrue(any("assumed" in value for value in result["report"]["limitations"]))
        self.assertIn("assumed", result["html_en"])


if __name__ == "__main__":
    unittest.main()
