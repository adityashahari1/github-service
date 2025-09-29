import re
import respx
from httpx import Response as HTTPXResponse

@respx.mock
def test_list_issues_forwards_link_header(client):
    # Match the outbound GitHub URL your code calls (with query)
    route = respx.get(re.compile(r"^https://api\.github\.com/repos/.+?/.+?/issues\?"))
    link = '<https://api.github.com/...page=2>; rel="next", <https://api.github.com/...page=5>; rel="last"'
    route.mock(return_value=HTTPXResponse(
        200,
        json=[{"number": 1, "title": "a", "state": "open"}],
        headers={"Link": link},
    ))

    r = client.get("/issues?state=open&per_page=30&page=1")
    assert r.status_code == 200
    assert "Link" in r.headers
    assert 'rel="next"' in r.headers["Link"]
