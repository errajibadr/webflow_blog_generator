"""Data models for the SEO blog generator."""

import base64
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, ClassVar, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class KeywordData(BaseModel):
    """Model for keyword data from CSV input."""

    database: str = Field(default="fr")
    keyword: str
    seed_keyword: Optional[str] = None
    page: Optional[str] = None
    topic: str
    page_type: str
    importance_in_cluster: Optional[float] = None
    tags: Optional[List[str]] = None
    volume: Optional[int] = None
    keyword_difficulty: Optional[float] = None
    cpc_usd: Optional[float] = None
    competitive_density: Optional[float] = None
    number_of_results: Optional[int] = None
    intent: Optional[str] = None
    serp_features: Optional[List[str]] = None
    trend: Optional[str] = None
    click_potential: Optional[str] = None
    content_references: Optional[dict[str, str]] = None
    competitors: Optional[dict[str, str]] = None

    def to_prompt_context(self) -> dict:
        """Convert keyword data to a format suitable for prompt context.

        Returns:
            dict: Keyword data formatted for prompt context
        """
        return {
            "primary_keyword": self.keyword,
            "importance_in_cluster": self.importance_in_cluster,
            "intent": self.intent or "informational",
            "volume": self.volume or 0,
            "competition": self.competitive_density or 0.0,
            "content_references": list(self.content_references.values())[:2]
            if self.content_references
            else [],
        }


class GeneratedImage(BaseModel):
    """Model representing a generated image."""

    model_config = ConfigDict(
        json_encoders={bytes: lambda v: base64.b64encode(v).decode("utf-8") if v else None}
    )

    image_data: bytes = Field(..., description="Raw image data")
    mime_type: str = Field(..., description="MIME type of the generated image")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata about the image"
    )

    # Map of MIME types to file extensions
    MIME_TO_EXT: ClassVar[dict[str, str]] = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "image/gif": ".gif",
    }

    @field_validator("image_data", mode="before")
    @classmethod
    def decode_base64(cls, v: Any) -> bytes:
        """Convert base64 string to bytes during deserialization."""
        if isinstance(v, str):
            try:
                # Remove any potential data URL prefix
                if "base64," in v:
                    v = v.split("base64,")[1]
                # Remove any whitespace and newlines
                v = v.strip()
                # Decode base64
                decoded = base64.b64decode(v)
                # Validate that the decoded data starts with known image headers
                if not any(
                    decoded.startswith(header)
                    for header in [
                        b"\xff\xd8\xff",  # JPEG
                        b"\x89PNG\r\n\x1a\n",  # PNG
                        b"RIFF",  # WebP
                        b"GIF87a",  # GIF
                        b"GIF89a",  # GIF
                    ]
                ):
                    raise ValueError("Invalid image data: does not match known image formats")
                return decoded
            except Exception as e:
                logger.error(f"Error decoding base64: {e}")
                raise ValueError(f"Invalid base64 string: {str(e)}")
        return v

    @field_validator("mime_type")
    @classmethod
    def validate_mime_type(cls, v: str) -> str:
        """Validate that the MIME type is supported."""
        if v not in cls.MIME_TO_EXT:
            raise ValueError(f"Unsupported MIME type: {v}")
        return v

    @property
    def size_bytes(self) -> int:
        """Get the size of the image data in bytes."""
        return len(self.image_data)

    def get_file_extension(self) -> str:
        """Get the appropriate file extension based on MIME type."""
        return self.MIME_TO_EXT.get(self.mime_type, ".jpg")

    def save_to_file(self, file_name: str, output_path: str | Path) -> Path:
        """Save the image data to a file.

        Args:
            output_path: Directory path where the image should be saved

        Returns:
            Path: Path to the saved image file
        """
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)

        # Generate a unique filename using timestamp and metadata
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{file_name}_{timestamp}{self.get_file_extension()}"
        file_path = output_path / filename

        try:
            # Validate image data before saving
            if len(self.image_data) < 100:  # Basic size check
                raise ValueError("Image data too small to be valid")

            with open(file_path, "wb") as f:
                f.write(self.image_data)

            # Verify the saved file
            if not file_path.exists() or file_path.stat().st_size < 100:
                raise ValueError("Failed to save valid image file")

            logger.info(f"Saved image to {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"Failed to save image to {file_path}: {e}")
            raise


class ImageDetail(BaseModel):
    """Model for image details."""

    placeholder: Optional[str] = None
    alt_text: str
    description: str
    url: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    generated_image: Optional[GeneratedImage] = None


class BlogArticle(BaseModel):
    """Model for a blog article."""

    title: str
    slug: str
    publication_date: str = Field(default_factory=lambda: datetime.now().strftime("%d/%m/%Y"))
    reading_time: str
    table_of_contents: Optional[str] = None
    content: str
    article_type: str
    article_types_secondary: List[str]
    article_summary: str
    title_tag: str
    meta_description: str
    # cluster_keyword_data: List[KeywordData]
    image_details: List[ImageDetail] = []
    json_ld: Optional[str] = None

    @classmethod
    def from_api_response(cls, response_data: dict) -> "BlogArticle":
        """Create a BlogArticle instance from API response data.

        Args:
            response_data: Dictionary containing the API response

        Returns:
            BlogArticle: Instantiated blog article
        """
        try:
            # Extract blog article data from the response
            blog_data = response_data.get("blog_article", {})
            if not blog_data:
                raise ValueError("No blog_article data found in response")

            # Create the BlogArticle instance
            # blog_data["cluster_keyword_data"] = [
            #     keyword_data for keyword_data in blog_data["cluster_keyword_data"]
            # ]
            return cls.model_validate(blog_data)

        except Exception as e:
            logger.error(f"Failed to deserialize blog article: {e}")
            raise

    def export_images(self, output_dir: str | Path) -> List[Path]:
        """Export all generated images to the specified directory.

        Args:
            output_dir: Base directory for image export

        Returns:
            List[Path]: List of paths to the exported images
        """
        output_dir = Path(output_dir)
        exported_paths = []

        for i, image_detail in enumerate(self.image_details, 1):
            if image_detail.generated_image:
                try:
                    # Create the images subdirectory if it doesn't exist
                    image_path = output_dir / "images"
                    saved_path = image_detail.generated_image.save_to_file(
                        f"{image_detail.placeholder}_{i}", image_path
                    )

                    # Update the URL field with the relative path
                    image_detail.generated_image.image_data = b""
                    image_detail.url = str(saved_path.relative_to(output_dir))
                    exported_paths.append(saved_path)

                except Exception as e:
                    logger.error(f"Failed to export image for {image_detail.alt_text}: {e}")
                    continue

        return exported_paths

    def to_json_dict(self) -> dict:
        """Convert the article to a JSON-serializable dictionary.

        Returns:
            dict: JSON-serializable dictionary
        """
        return {
            "Titre": self.title,
            "Slug": self.slug,
            "Date de publication": self.publication_date,
            "Durée de lecture": self.reading_time,
            "Contenu article": self.content,
            "Type d'article": self.article_type,
            "Type d'article 2-8": ", ".join(self.article_types_secondary),
            "Résumé de l'article": self.article_summary,
            "Balise title": self.title_tag,
            "META DESCRIPTION": self.meta_description,
            "JSON_LD": self.json_ld,
        }
