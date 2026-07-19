import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from apilayer.base import APILayerConfig  # noqa: E402
from apilayer.enrichment import (  # noqa: E402
    attach_enrichment,
    enrich_with_site_capture,
    enrich_with_weather,
)
from apilayer.screenshotlayer import ScreenshotlayerClient  # noqa: E402
from apilayer.weatherstack import WeatherstackClient  # noqa: E402
from higgsfield.models import Scene  # noqa: E402
from test_apilayer_base import FakeResponse, FakeSession  # noqa: E402


def make_scene():
    return Scene(id="scene-01", prompt="an establishing shot")


def test_attach_enrichment_merges_without_clobbering():
    scene = make_scene()
    attach_enrichment(scene, weather={"temperature_c": 10})
    attach_enrichment(scene, site_capture={"url": "https://example.com"})
    assert scene.params["enrichment"] == {
        "weather": {"temperature_c": 10},
        "site_capture": {"url": "https://example.com"},
    }


def test_enrich_with_weather_reads_current_conditions():
    response = FakeResponse(
        200,
        {
            "success": True,
            "current": {"temperature": 12, "weather_descriptions": ["Overcast"]},
        },
    )
    session = FakeSession([response])
    config = APILayerConfig(access_key="key_test", base_url=WeatherstackClient.default_base_url)
    client = WeatherstackClient(config, session=session)

    scene = enrich_with_weather(make_scene(), client, "Berlin")

    assert scene.params["enrichment"]["weather"] == {
        "location": "Berlin",
        "description": "Overcast",
        "temperature_c": 12,
    }


def test_enrich_with_site_capture_writes_image(tmp_path):
    response = FakeResponse(200, headers={"content-type": "image/png"}, content=b"\x89PNG")
    session = FakeSession([response])
    config = APILayerConfig(access_key="key_test", base_url=ScreenshotlayerClient.default_base_url)
    client = ScreenshotlayerClient(config, session=session)

    scene = enrich_with_site_capture(make_scene(), client, "https://example.com", tmp_path)

    capture = scene.params["enrichment"]["site_capture"]
    assert capture["url"] == "https://example.com"
    image_path = Path(capture["image_path"])
    assert image_path.exists()
    assert image_path.read_bytes() == b"\x89PNG"
