import io

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

import pytest
from PIL import Image

from apps.article.models import Article


def png_upload(name="photo.png", size=(40, 30)):
    buffer = io.BytesIO()
    Image.new("RGB", size, "red").save(buffer, format="PNG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/png")


def image_field():
    return Article._meta.get_field("image").formfield()


def test_valid_image_is_accepted():
    cleaned = image_field().clean(png_upload())

    assert cleaned.image.size == (40, 30)
    assert cleaned.content_type == "image/png"


def test_non_image_file_is_rejected():
    fake = SimpleUploadedFile("photo.png", b"not an image", content_type="image/png")

    with pytest.raises(ValidationError) as error:
        image_field().clean(fake)

    assert error.value.code == "invalid_image"


@pytest.mark.django_db
def test_article_image_is_stored(settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)

    article = Article.objects.create(
        title="Avec image", body="Corps", image=png_upload()
    )

    article.refresh_from_db()
    assert article.image.name.startswith("articles/")
    assert article.image.width == 40
    assert article.image.height == 30
