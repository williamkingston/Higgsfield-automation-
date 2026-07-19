"""One focused test per APILayer product client, checking that its methods hit
the right path with the right params. Auth injection, retries, and error
parsing are already covered by test_apilayer_base.py's shared base-client
tests — these just verify each product's thin endpoint-mapping layer.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from apilayer.aviationstack import AviationstackClient  # noqa: E402
from apilayer.base import APILayerConfig  # noqa: E402
from apilayer.coinlayer import CoinlayerClient  # noqa: E402
from apilayer.currencylayer import CurrencylayerClient  # noqa: E402
from apilayer.fixer import FixerClient  # noqa: E402
from apilayer.giflayer import GiflayerClient  # noqa: E402
from apilayer.ipstack import IpstackClient  # noqa: E402
from apilayer.mailboxlayer import MailboxlayerClient  # noqa: E402
from apilayer.marketstack import MarketstackClient  # noqa: E402
from apilayer.mediastack import MediastackClient  # noqa: E402
from apilayer.numverify import NumverifyClient  # noqa: E402
from apilayer.pdflayer import PdflayerClient  # noqa: E402
from apilayer.positionstack import PositionstackClient  # noqa: E402
from apilayer.scrapestack import ScrapestackClient  # noqa: E402
from apilayer.screenshotlayer import ScreenshotlayerClient  # noqa: E402
from apilayer.serpstack import SerpstackClient  # noqa: E402
from apilayer.streetlayer import StreetlayerClient  # noqa: E402
from apilayer.userstack import UserstackClient  # noqa: E402
from apilayer.vatlayer import VatlayerClient  # noqa: E402
from apilayer.weatherstack import WeatherstackClient  # noqa: E402
from test_apilayer_base import FakeResponse, FakeSession  # noqa: E402


def make_client(cls, *, response, base_url=None):
    config = APILayerConfig(access_key="key_test", base_url=base_url or cls.default_base_url)
    session = FakeSession([response])
    return cls(config, session=session), session


def test_weatherstack_current():
    client, session = make_client(WeatherstackClient, response=FakeResponse(200, {"success": True}))
    client.current("Berlin", units="m")
    call = session.calls[0]
    assert call["url"] == "http://api.weatherstack.com/current"
    assert call["params"] == {"query": "Berlin", "units": "m", "access_key": "key_test"}


def test_aviationstack_flights():
    response = FakeResponse(200, {"success": True})
    client, session = make_client(AviationstackClient, response=response)
    client.flights(flight_iata="BA123", limit=10)
    call = session.calls[0]
    assert call["url"] == "http://api.aviationstack.com/v1/flights"
    assert call["params"]["flight_iata"] == "BA123"
    assert call["params"]["limit"] == 10


def test_fixer_historical_uses_date_in_path():
    client, session = make_client(FixerClient, response=FakeResponse(200, {"success": True}))
    client.historical("2020-01-01", base="USD")
    call = session.calls[0]
    assert call["url"] == "http://data.fixer.io/api/2020-01-01"
    assert call["params"] == {"base": "USD", "access_key": "key_test"}


def test_currencylayer_convert():
    response = FakeResponse(200, {"success": True})
    client, session = make_client(CurrencylayerClient, response=response)
    client.convert("USD", "EUR", 100)
    call = session.calls[0]
    assert call["url"] == "http://api.currencylayer.com/convert"
    assert call["params"]["from"] == "USD"
    assert call["params"]["to"] == "EUR"
    assert call["params"]["amount"] == 100


def test_marketstack_end_of_day():
    client, session = make_client(MarketstackClient, response=FakeResponse(200, {"success": True}))
    client.end_of_day(["AAPL", "MSFT"], limit=5)
    call = session.calls[0]
    assert call["url"] == "http://api.marketstack.com/v1/eod"
    assert call["params"]["symbols"] == "AAPL,MSFT"
    assert call["params"]["limit"] == 5


def test_positionstack_reverse_geocode():
    response = FakeResponse(200, {"success": True})
    client, session = make_client(PositionstackClient, response=response)
    client.reverse_geocode(52.5, 13.4)
    call = session.calls[0]
    assert call["url"] == "http://api.positionstack.com/v1/reverse"
    assert call["params"]["query"] == "52.5,13.4"


def test_ipstack_lookup_defaults_to_check():
    client, session = make_client(IpstackClient, response=FakeResponse(200, {"success": True}))
    client.lookup()
    call = session.calls[0]
    assert call["url"] == "http://api.ipstack.com/check"


def test_vatlayer_validate():
    client, session = make_client(VatlayerClient, response=FakeResponse(200, {"success": True}))
    client.validate("DE123456789")
    call = session.calls[0]
    assert call["url"] == "http://apilayer.net/api/validate"
    assert call["params"]["vat_number"] == "DE123456789"


def test_mailboxlayer_validate_encodes_booleans():
    client, session = make_client(MailboxlayerClient, response=FakeResponse(200, {"success": True}))
    client.validate("test@example.com", smtp=False)
    call = session.calls[0]
    assert call["params"]["email"] == "test@example.com"
    assert call["params"]["smtp"] == 0
    assert call["params"]["format"] == 1


def test_numverify_validate():
    client, session = make_client(NumverifyClient, response=FakeResponse(200, {"success": True}))
    client.validate("14158586273", country_code="US")
    call = session.calls[0]
    assert call["url"] == "http://apilayer.net/api/validate"
    assert call["params"]["country_code"] == "US"


def test_userstack_lookup():
    client, session = make_client(UserstackClient, response=FakeResponse(200, {"success": True}))
    client.lookup("Mozilla/5.0")
    call = session.calls[0]
    assert call["params"]["ua"] == "Mozilla/5.0"


def test_serpstack_search():
    client, session = make_client(SerpstackClient, response=FakeResponse(200, {"success": True}))
    client.search("higgsfield ai", gl="us")
    call = session.calls[0]
    assert call["params"]["query"] == "higgsfield ai"
    assert call["params"]["gl"] == "us"


def test_scrapestack_scrape_returns_text():
    response = FakeResponse(200, headers={"content-type": "text/html"}, text="<html>ok</html>")
    client, session = make_client(ScrapestackClient, response=response)
    result = client.scrape("https://example.com", render_js=True)
    assert result == "<html>ok</html>"
    call = session.calls[0]
    assert call["params"]["url"] == "https://example.com"
    assert call["params"]["render_js"] == 1


def test_screenshotlayer_capture_returns_bytes():
    response = FakeResponse(200, headers={"content-type": "image/png"}, content=b"\x89PNG")
    client, session = make_client(ScreenshotlayerClient, response=response)
    result = client.capture("https://example.com")
    assert result == b"\x89PNG"
    call = session.calls[0]
    assert call["url"] == "http://api.screenshotlayer.com/api/capture"


def test_giflayer_convert():
    client, session = make_client(GiflayerClient, response=FakeResponse(200, {"success": True}))
    client.convert("https://example.com/video.mp4", start=1.5)
    call = session.calls[0]
    assert call["params"]["video_url"] == "https://example.com/video.mp4"
    assert call["params"]["start"] == 1.5


def test_pdflayer_convert_url_returns_bytes():
    response = FakeResponse(200, headers={"content-type": "application/pdf"}, content=b"%PDF-1.4")
    client, session = make_client(PdflayerClient, response=response)
    result = client.convert_url("https://example.com")
    assert result == b"%PDF-1.4"


def test_coinlayer_historical_uses_date_in_path():
    client, session = make_client(CoinlayerClient, response=FakeResponse(200, {"success": True}))
    client.historical("2020-01-01", symbols=["BTC"])
    call = session.calls[0]
    assert call["url"] == "http://api.coinlayer.com/2020-01-01"
    assert call["params"]["symbols"] == "BTC"


def test_mediastack_news():
    client, session = make_client(MediastackClient, response=FakeResponse(200, {"success": True}))
    client.news(keywords="ai video", countries=["us", "gb"])
    call = session.calls[0]
    assert call["params"]["keywords"] == "ai video"
    assert call["params"]["countries"] == "us,gb"


def test_streetlayer_autocomplete():
    client, session = make_client(StreetlayerClient, response=FakeResponse(200, {"success": True}))
    client.autocomplete("221b Baker", country="GB")
    call = session.calls[0]
    assert call["url"] == "http://api.streetlayer.com/api/autocomplete"
    assert call["params"]["country"] == "GB"
