from vera.config import Settings


def test_lab_urls_in_settings():
    s = Settings()
    assert "postgresql" in s.vera_postgres_url
    assert "postgresql" in s.vera_timescale_url
