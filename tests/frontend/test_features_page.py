from tests.frontend.conftest import parse_html


def test_features_page_renders_logs_toggle(client, logged_in_user):
    response = client.get("/admin/features")
    soup = parse_html(response)

    assert response.status_code == 200
    assert soup.select_one("h1.h2").get_text(strip=True) == "Features"
    assert soup.select_one("input.feature-toggle") is None
    assert soup.select_one("a[href='/features/log']") is not None
    assert soup.select_one("a[href='/features/leaderboard']") is not None
    assert soup.select_one("a[href='/features/discussion']") is not None
    assert len(soup.select("#featureList .card")) == 3
    assert soup.find(string=lambda text: text and "instance-level functionality" in text) is not None
