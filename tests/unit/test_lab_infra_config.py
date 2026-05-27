from raip.config import Settings


def test_lab_urls_in_settings():
    s = Settings()
    assert "postgresql" in s.raip_postgres_url
    assert "postgresql" in s.raip_timescale_url
