import unittest

from disclosure_sources import HouseDisclosureSource


class HouseDisclosureSourceTest(unittest.TestCase):
    def test_only_non_secret_response_metadata_is_retained(self) -> None:
        metadata = HouseDisclosureSource._safe_headers(
            {
                "ETag": '"abc"',
                "Last-Modified": "Wed, 01 Oct 2026 10:00:00 GMT",
                "Content-Type": "application/pdf",
                "Authorization": "Bearer should-never-be-retained",
                "Set-Cookie": "session=should-never-be-retained",
            }
        )

        self.assertEqual(
            metadata,
            {
                "etag": '"abc"',
                "last-modified": "Wed, 01 Oct 2026 10:00:00 GMT",
                "content-type": "application/pdf",
            },
        )

    def test_official_locators_reject_unbounded_years_and_non_numeric_document_ids(self) -> None:
        source = HouseDisclosureSource()

        with self.assertRaises(ValueError):
            source.fetch_index(1900)
        with self.assertRaises(ValueError):
            source.fetch_index(2100)
        with self.assertRaises(ValueError):
            source.fetch_filing(2025, "../../secret")


if __name__ == "__main__":
    unittest.main()
