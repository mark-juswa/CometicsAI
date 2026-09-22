import base64
from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image

from app.main import MAX_FILE_BYTES, app


client = TestClient(app)


def image_bytes(format: str = "PNG", size: tuple[int, int] = (128, 96)) -> bytes:
    image = Image.new("RGB", size, "#8aafbb")
    buffer = BytesIO()
    image.save(buffer, format=format)
    return buffer.getvalue()


def post_image(data: bytes, content_type: str = "image/png", style_id: str = "bob"):
    return client.post(
        "/generate",
        data={"style_id": style_id},
        files={"image": ("portrait.png", data, content_type)},
    )


def test_health_and_prototype_styles():
    assert client.get("/health").json() == {"status": "ok", "generator": "mock"}
    styles = client.get("/styles")
    assert styles.status_code == 200
    assert len(styles.json()) == 6
    assert {style["status"] for style in styles.json()} == {"prototype"}


def test_generate_returns_normalized_mock_image_and_style():
    response = post_image(image_bytes())
    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "completed"
    assert result["generator"] == "mock"
    assert result["style"]["id"] == "bob"
    assert result["image"]["content_type"] == "image/jpeg"
    assert (result["image"]["width"], result["image"]["height"]) == (128, 96)
    encoded = result["image"]["data_url"].split(",", 1)[1]
    with Image.open(BytesIO(base64.b64decode(encoded))) as output:
        assert output.mode == "RGB"
        assert output.size == (128, 96)


def test_generate_rejects_missing_image_and_style():
    assert client.post("/generate", data={"style_id": "bob"}).status_code == 422
    assert post_image(image_bytes(), style_id="unknown").status_code == 400


def test_generate_rejects_invalid_type_content_and_size():
    assert post_image(b"hello", "text/plain").status_code == 415
    assert post_image(b"hello").status_code == 400
    assert post_image(image_bytes("JPEG"), "image/png").status_code == 415
    assert post_image(image_bytes(size=(48, 48))).status_code == 422
    assert post_image(b"x" * (MAX_FILE_BYTES + 1)).status_code == 413


def test_exif_orientation_is_applied():
    image = Image.new("RGB", (100, 64), "blue")
    exif = Image.Exif()
    exif[274] = 6
    buffer = BytesIO()
    image.save(buffer, format="JPEG", exif=exif)
    response = post_image(buffer.getvalue(), "image/jpeg")
    assert response.status_code == 200
    assert (response.json()["image"]["width"], response.json()["image"]["height"]) == (64, 100)


def test_local_frontend_origin_is_allowed():
    response = client.options(
        "/generate",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
