import json
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from evidence_merge import build_brief, canonical_url, merge_records, parse_source


class EvidenceMergeTests(unittest.TestCase):
    def test_dedupe_and_layer_merge(self):
        sample = [
            {"url": "https://youtu.be/abc?utm_source=test", "platform": "youtube", "provider": "web",
             "status": "METADATA_ONLY", "layers": {"metadata": "CONTENT_READ"}},
            {"url": "https://youtu.be/abc", "platform": "youtube", "provider": "local-tool",
             "status": "CONTENT_READ", "layers": {"transcript": "CONTENT_READ"},
             "summary": "Real subtitle text"},
        ]
        result = merge_records(sample)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["providers"], ["local-tool", "web"])
        self.assertEqual(result[0]["status"], "CONTENT_READ")
        self.assertEqual(len(result[0]["layers"]), 2)
        self.assertIn("transcript:CONTENT_READ", build_brief(result))

    def test_url_strips_tracking_not_youtube_id(self):
        self.assertEqual(canonical_url("http://youtube.com/watch?v=example&utm_medium=social"),
                         "https://youtube.com/watch?v=example")

    def test_rejects_secret_and_userinfo(self):
        for url in ["https://example.com/?token=secret", "https://user:pass@example.com/post",
                    "file:///tmp/a", "http://localhost/path", "http://192.168.1.1/path"]:
            with self.assertRaises(ValueError):
                canonical_url(url)

    def test_invalid_retrieval_status(self):
        with self.assertRaises(ValueError):
            merge_records([{"url": "https://reddit.com/r/aviation", "provider": "web",
                            "platform": "reddit", "status": "I_WATCHED_THE_VIDEO"}])

    def test_conflicting_claims_do_not_inherit_truth(self):
        rows = merge_records([
            {"url": "https://example.com/post", "platform": "web", "provider": "web",
             "status": "PARTIAL", "claim_status": "Unverified"},
            {"url": "https://example.com/post", "platform": "web", "provider": "scraper",
             "status": "CONTENT_READ", "claim_status": "Verified"}
        ])
        self.assertEqual(rows[0]["claim_status"], "Unverified")
        self.assertTrue(rows[0]["lead_only"])

    def test_youtube_short_and_watch_aliases(self):
        urls = [
            "https://youtu.be/abc?si=anything",
            "https://www.youtube.com/watch?v=abc&list=playlist",
            "https://m.youtube.com/shorts/abc?feature=share",
            "https://youtube.com/embed/abc",
        ]
        self.assertEqual({canonical_url(u) for u in urls}, {"https://youtube.com/watch?v=abc"})

    def test_reddit_old_www_and_slug(self):
        urls = [
            "https://old.reddit.com/r/aviation/comments/abc123/topic-one/",
            "https://www.reddit.com/r/aviation/comments/abc123/topic-two/?sort=new",
            "https://reddit.com/r/aviation/comments/abc123",
        ]
        self.assertEqual({canonical_url(u) for u in urls}, {"https://reddit.com/r/aviation/comments/abc123"})

    def test_twitter_x_aliases(self):
        urls = [
            "https://twitter.com/UserName/status/12345?s=20",
            "https://www.x.com/username/status/12345/photo/1",
            "https://x.com/username/status/12345",
        ]
        self.assertEqual({canonical_url(u) for u in urls}, {"https://x.com/i/web/status/12345"})

    def test_instagram_reel_post_aliases(self):
        urls = [
            "https://www.instagram.com/reel/CBA_abc/?igsh=foo",
            "https://instagram.com/p/CBA_abc",
            "https://m.instagram.com/tv/CBA_abc",
        ]
        self.assertEqual({canonical_url(u) for u in urls}, {"https://instagram.com/p/CBA_abc"})

    def test_www_bare_domains(self):
        self.assertEqual(canonical_url("https://www.example.com/blog/post/"),
                         canonical_url("https://example.com/blog/post"))

    def test_different_ids_are_not_merged(self):
        self.assertNotEqual(canonical_url("https://youtu.be/abc"),
                            canonical_url("https://youtube.com/shorts/def"))
        self.assertNotEqual(canonical_url("https://instagram.com/p/abc"),
                            canonical_url("https://instagram.com/p/def"))

    def test_merge_real_aliases_across_providers(self):
        urls = ["https://youtu.be/abc", "https://youtube.com/shorts/abc",
                "https://old.reddit.com/r/aviation/comments/abc123/title",
                "https://www.reddit.com/r/aviation/comments/abc123/new",
                "https://twitter.com/name/status/12345", "https://x.com/name/status/12345",
                "https://instagram.com/reel/ABC", "https://www.instagram.com/p/ABC"]
        records = [{"url": u, "platform": "test", "provider": f"p{i}",
                    "status": "CONTENT_READ"} for i, u in enumerate(urls)]
        result = merge_records(records)
        self.assertEqual(len(result), 4)
        self.assertTrue(all(len(row["providers"]) == 2 for row in result))
        self.assertTrue(all(row["lead_only"] for row in result))

    def test_reddit_distinct_comments_and_post_do_not_collapse(self):
        urls = [
            "https://reddit.com/r/aviation/comments/abc123/title/",  # post
            "https://reddit.com/r/aviation/comments/abc123/title/kx1aaa/",
            "https://reddit.com/r/aviation/comments/abc123/title/kx2bbb/",
        ]
        normalized = [canonical_url(url) for url in urls]
        self.assertEqual(len(set(normalized)), 3)
        rows = merge_records([
            {"url": url, "platform": "reddit", "provider": "local-tool", "status": "CONTENT_READ",
             "summary": f"Comment {n}"} for n, url in enumerate(urls)
        ])
        self.assertEqual(len(rows), 3)
        self.assertEqual({r["summary"] for r in rows}, {"Comment 0", "Comment 1", "Comment 2"})

    def test_reddit_same_comment_different_slug_merges(self):
        links = [
            "https://old.reddit.com/r/aviation/comments/abc123/old-title/KX1AAA/?context=3",
            "https://www.reddit.com/r/aviation/comments/abc123/new-title/kx1aaa/",
            "https://reddit.com/r/aviation/comments/abc123/any-title/kx2bbb",
        ]
        self.assertEqual(canonical_url(links[0]), canonical_url(links[1]))
        self.assertNotEqual(canonical_url(links[0]), canonical_url(links[2]))
        rows = merge_records([{"url": link, "platform": "reddit", "provider": str(n),
                               "status": "CONTENT_READ"} for n, link in enumerate(links)])
        self.assertEqual(len(rows), 2)
        self.assertEqual(sorted(len(r["providers"]) for r in rows), [1, 2])

    def test_reddit_comment_query_id_preserved(self):
        a = canonical_url("https://reddit.com/r/aviation/comments/abc123/topic?comment=kx1aaa")
        b = canonical_url("https://reddit.com/r/aviation/comments/abc123/topic/kx1aaa")
        c = canonical_url("https://reddit.com/r/aviation/comments/abc123/topic")
        self.assertEqual(a, b)
        self.assertNotEqual(a, c)

    def test_youtube_playlist_embed_is_not_a_fake_video(self):
        playlist = canonical_url("https://www.youtube.com/embed/videoseries?list=PL123")
        self.assertEqual(playlist, "https://youtube.com/embed/videoseries?list=PL123")
        self.assertNotEqual(playlist, canonical_url("https://youtube.com/watch?v=videoseries"))
        self.assertNotEqual(playlist, canonical_url("https://youtube.com/embed/videoseries?list=PL456"))

    def test_instagram_username_reel_alias(self):
        links = ["https://instagram.com/person/reel/ABC_123",
                 "https://www.instagram.com/reel/ABC_123",
                 "https://instagram.com/p/ABC_123"]
        self.assertEqual(len({canonical_url(u) for u in links}), 1)

    def test_facebook_mobile_alias(self):
        self.assertEqual(canonical_url("https://m.facebook.com/example/posts/abc?utm_source=foo"),
                         canonical_url("https://facebook.com/example/posts/abc"))

    def test_x_generic_and_user_status_alias(self):
        links = ["https://x.com/i/web/status/1234567890",
                 "https://twitter.com/SomeUser/status/1234567890?s=20",
                 "https://www.x.com/other_name/status/1234567890"]
        self.assertEqual(len({canonical_url(u) for u in links}), 1)
        self.assertNotEqual(canonical_url(links[0]),
                            canonical_url("https://x.com/i/web/status/9876543210"))

    def test_unrecognized_reddit_path_retained(self):
        self.assertNotEqual(
            canonical_url("https://reddit.com/r/aviation/comments/abc123/topic/kx1aaa/extra"),
            canonical_url("https://reddit.com/r/aviation/comments/abc123/topic/kx1aaa"))

    def test_legacy_labels_are_migrated_not_verified(self):
        row = merge_records([{
            "url": "https://youtu.be/abc", "platform": "youtube", "provider": "legacy",
            "status": "CONTENT_VERIFIED", "claim_status": "CONFIRMED_PRIMARY",
            "layers": {"transcript": "CONTENT_VERIFIED"}, "lead_only": False,
        }])[0]
        self.assertEqual(row["status"], "CONTENT_READ")
        self.assertEqual(row["claim_status"], "Verified")  # Reported only, not adjudicated
        self.assertTrue(row["lead_only"])
        self.assertEqual(row["layers"]["transcript"], "CONTENT_READ")

    def test_unknown_claim_and_lead_only_types_fail_closed(self):
        base = {"url": "https://youtu.be/abc", "platform": "youtube", "provider": "test", "status": "PARTIAL"}
        with self.assertRaises(ValueError):
            merge_records([{**base, "claim_status": "TRUE"}])
        with self.assertRaises(ValueError):
            merge_records([{**base, "lead_only": "false"}])

    def test_jsonl(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "evidence.jsonl"
            path.write_text(json.dumps({"url": "https://reddit.com/a", "platform": "reddit",
                                        "provider": "web", "status": "PARTIAL"}) + "\n", encoding="utf-8")
            self.assertEqual(len(parse_source(path)), 1)


if __name__ == "__main__":
    unittest.main()
