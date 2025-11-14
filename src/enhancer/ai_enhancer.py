"""
Dual-AI Listing Enhancer
=========================
Uses both OpenAI and Anthropic Claude to enhance listings with:
- AI-generated descriptions
- Title optimization
- Photo analysis
- Keyword extraction
- Category suggestions
"""

import os
import base64
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import requests
from pathlib import Path

from ..schema.unified_listing import (
    UnifiedListing,
    Photo,
    SEOData,
    Category,
    ItemSpecifics,
)


class AIEnhancer:
    """
    Dual-AI enhancer using both OpenAI and Anthropic.

    Strategy:
    - OpenAI GPT-4 Vision: Photo analysis and initial description
    - Anthropic Claude: Enhanced copywriting and SEO optimization
    - Combined: Best of both for maximum listing quality
    """

    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        use_openai: bool = True,
        use_anthropic: bool = True,
    ):
        """
        Initialize AI enhancer.

        Args:
            openai_api_key: OpenAI API key
            anthropic_api_key: Anthropic API key
            use_openai: Enable OpenAI enhancement
            use_anthropic: Enable Anthropic enhancement
        """
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        self.use_openai = use_openai and self.openai_api_key is not None
        self.use_anthropic = use_anthropic and self.anthropic_api_key is not None

        if not (self.use_openai or self.use_anthropic):
            raise ValueError(
                "At least one AI provider must be enabled with valid API key"
            )

    def _encode_image_to_base64(self, image_path: str) -> str:
        """Encode local image to base64"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    def _get_image_mime_type(self, image_path: str) -> str:
        """Get MIME type from file extension"""
        ext = Path(image_path).suffix.lower()
        mime_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        return mime_types.get(ext, "image/jpeg")

    def analyze_photos_openai(self, photos: List[Photo]) -> Dict[str, Any]:
        """
        Analyze photos using OpenAI GPT-4 Vision.

        Returns:
            Dictionary with photo analysis, suggested title, description, keywords
        """
        if not self.use_openai:
            return {}

        # Prepare images for vision analysis
        image_contents = []
        for photo in photos[:4]:  # Limit to 4 photos to save tokens
            if photo.local_path:
                image_b64 = self._encode_image_to_base64(photo.local_path)
                mime_type = self._get_image_mime_type(photo.local_path)
                image_contents.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime_type};base64,{image_b64}"
                    }
                })
            elif photo.url:
                image_contents.append({
                    "type": "image_url",
                    "image_url": {"url": photo.url}
                })

        # Build prompt
        prompt = """Analyze these product images and provide:

1. **Item Description**: Detailed description of the item (2-3 paragraphs)
2. **Title**: Concise, keyword-rich title (under 80 characters)
3. **Keywords**: 10-15 relevant search keywords
4. **Category**: Suggested category (e.g., "Electronics > Cameras", "Clothing > Women's > Dresses")
5. **Condition Details**: Specific condition observations (flaws, wear, etc.)
6. **Key Features**: Bullet points of notable features or selling points

Format your response as JSON:
{
  "description": "...",
  "title": "...",
  "keywords": ["...", "..."],
  "category": "...",
  "condition_notes": "...",
  "features": ["...", "..."]
}"""

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    *image_contents,
                ]
            }
        ]

        # Call OpenAI API
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": "gpt-4o",  # GPT-4 Vision
            "messages": messages,
            "max_tokens": 1500,
            "temperature": 0.7,
        }

        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
        )

        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]

            # Parse JSON response
            import json
            try:
                # Try to extract JSON from markdown code blocks if present
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()

                analysis = json.loads(content)
                return analysis
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                return {"raw_response": content}
        else:
            raise Exception(f"OpenAI API error: {response.text}")

    def enhance_with_claude(
        self,
        initial_data: Dict[str, Any],
        target_platform: str = "general",
    ) -> Dict[str, Any]:
        """
        Enhance listing copy using Anthropic Claude.

        Args:
            initial_data: Initial data from photo analysis
            target_platform: Target platform (ebay, mercari, general)

        Returns:
            Enhanced description, title, and SEO data
        """
        if not self.use_anthropic:
            return initial_data

        # Build enhancement prompt
        platform_context = {
            "ebay": "eBay (focus on detailed specs, trust-building, and search keywords)",
            "mercari": "Mercari (casual, mobile-friendly, highlight condition and value)",
            "general": "general e-commerce",
        }

        context = platform_context.get(target_platform.lower(), "general e-commerce")

        prompt = f"""You are an expert e-commerce copywriter. Enhance this listing for {context}.

Initial data:
- Title: {initial_data.get('title', '')}
- Description: {initial_data.get('description', '')}
- Keywords: {', '.join(initial_data.get('keywords', []))}
- Features: {', '.join(initial_data.get('features', []))}

Please provide:
1. **Optimized Title**: Compelling, keyword-rich (80 chars max)
2. **Enhanced Description**: Professional, persuasive, highlights value
3. **SEO Keywords**: Top 15 keywords for search optimization
4. **Search Terms**: Alternative search phrases buyers might use

Format as JSON:
{{
  "title": "...",
  "description": "...",
  "keywords": ["...", "..."],
  "search_terms": ["...", "..."]
}}"""

        headers = {
            "x-api-key": self.anthropic_api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        payload = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 2000,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        }

        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=payload,
        )

        if response.status_code == 200:
            result = response.json()
            content = result["content"][0]["text"]

            # Parse JSON response
            import json
            try:
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()

                enhanced = json.loads(content)
                return enhanced
            except json.JSONDecodeError:
                return {"raw_response": content}
        else:
            raise Exception(f"Anthropic API error: {response.text}")

    def enhance_listing(
        self,
        listing: UnifiedListing,
        target_platform: str = "general",
        force: bool = False,
    ) -> UnifiedListing:
        """
        Complete AI enhancement workflow.

        Args:
            listing: UnifiedListing to enhance
            target_platform: Target platform for optimization
            force: Force re-enhancement even if already enhanced

        Returns:
            Enhanced UnifiedListing
        """
        if listing.ai_enhanced and not force:
            # Already enhanced, skip
            return listing

        # Step 1: Analyze photos with OpenAI (if available)
        openai_analysis = {}
        if self.use_openai and listing.photos:
            try:
                openai_analysis = self.analyze_photos_openai(listing.photos)
            except Exception as e:
                print(f"OpenAI analysis failed: {e}")

        # Step 2: Enhance with Claude (if available)
        enhanced_data = openai_analysis
        if self.use_anthropic:
            try:
                enhanced_data = self.enhance_with_claude(openai_analysis, target_platform)
            except Exception as e:
                print(f"Claude enhancement failed: {e}")

        # Step 3: Apply enhancements to listing
        if enhanced_data:
            # Update description if provided
            if enhanced_data.get("description"):
                listing.description = enhanced_data["description"]

            # Update title if provided
            if enhanced_data.get("title"):
                listing.title = enhanced_data["title"]

            # Update SEO data
            if enhanced_data.get("keywords"):
                listing.seo_data.keywords = enhanced_data["keywords"]

            if enhanced_data.get("search_terms"):
                listing.seo_data.search_terms = enhanced_data["search_terms"]

            # Update category if suggested
            if enhanced_data.get("category"):
                category_parts = enhanced_data["category"].split(" > ")
                if not listing.category:
                    listing.category = Category(
                        primary=category_parts[0],
                        subcategory=category_parts[1] if len(category_parts) > 1 else None,
                    )

            # Mark as AI enhanced
            listing.ai_enhanced = True
            listing.ai_enhancement_timestamp = datetime.now()
            listing.ai_provider = []
            if self.use_openai:
                listing.ai_provider.append("OpenAI")
            if self.use_anthropic:
                listing.ai_provider.append("Anthropic")
            listing.ai_provider = " + ".join(listing.ai_provider)

        return listing

    @classmethod
    def from_env(cls) -> "AIEnhancer":
        """
        Create enhancer from environment variables.

        Expected variables:
            - OPENAI_API_KEY (optional)
            - ANTHROPIC_API_KEY (optional)
        """
        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        )


def enhance_listing(
    listing: UnifiedListing,
    target_platform: str = "general",
    force: bool = False,
) -> UnifiedListing:
    """
    Convenience function to enhance a listing.

    Args:
        listing: UnifiedListing to enhance
        target_platform: Target platform
        force: Force re-enhancement

    Returns:
        Enhanced listing
    """
    enhancer = AIEnhancer.from_env()
    return enhancer.enhance_listing(listing, target_platform, force)
