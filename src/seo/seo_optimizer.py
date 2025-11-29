"""
SEO Automation Module for AI Cross-Poster
Generates SEO-optimized titles, descriptions, and keywords for multi-platform listings
"""

import re
from typing import Dict, List, Optional, Any
from datetime import datetime
import os


class SEOOptimizer:
    """AI-powered SEO optimization for marketplace listings"""

    # Common marketplace keywords by category
    CATEGORY_KEYWORDS = {
        'clothing': [
            'vintage', 'retro', 'brand new', 'authentic', 'designer',
            'streetwear', 'fashion', 'style', 'trendy', 'classic'
        ],
        'electronics': [
            'brand new', 'sealed', 'authentic', 'certified', 'warranty',
            'genuine', 'original', 'latest', 'upgraded', 'premium'
        ],
        'collectibles': [
            'rare', 'vintage', 'limited edition', 'collectible', 'mint condition',
            'authenticated', 'graded', 'first edition', 'signed', 'exclusive'
        ],
        'cards': [
            'rare', 'mint', 'near mint', 'PSA', 'graded', 'holographic',
            'first edition', 'limited', 'rookie card', 'autograph'
        ],
        'toys': [
            'vintage', 'rare', 'collectible', 'mint in box', 'sealed',
            'limited edition', 'retro', 'classic', 'exclusive', 'discontinued'
        ],
        'home': [
            'modern', 'vintage', 'retro', 'antique', 'handmade',
            'designer', 'unique', 'custom', 'quality', 'premium'
        ]
    }

    # SEO power words that increase click-through rates
    POWER_WORDS = [
        'Amazing', 'Exclusive', 'Limited', 'Rare', 'Authentic',
        'Premium', 'Quality', 'Perfect', 'Stunning', 'Beautiful',
        'Gorgeous', 'Unique', 'Special', 'Must-Have', 'Popular'
    ]

    # Condition keywords
    CONDITION_KEYWORDS = {
        'new': ['Brand New', 'New with Tags', 'Never Used', 'Sealed', 'Mint'],
        'like new': ['Like New', 'Excellent', 'Near Mint', 'Barely Used'],
        'used': ['Pre-Owned', 'Gently Used', 'Good Condition', 'Clean'],
        'fair': ['Fair Condition', 'Has Wear', 'Used'],
        'poor': ['As-Is', 'For Parts', 'Needs Repair']
    }

    def __init__(self, ai_client=None):
        """
        Initialize SEO Optimizer

        Args:
            ai_client: Optional AI client for advanced optimization
        """
        self.ai_client = ai_client

    def detect_category(self, title: str, description: str = "") -> str:
        """
        Auto-detect item category from title and description

        Args:
            title: Item title
            description: Item description

        Returns:
            Detected category
        """
        text = (title + " " + description).lower()

        # Category detection patterns
        category_patterns = {
            'clothing': ['shirt', 'pants', 'dress', 'jacket', 'shoes', 'clothing', 'jeans', 'hoodie'],
            'electronics': ['phone', 'laptop', 'tablet', 'camera', 'headphones', 'gaming', 'console'],
            'collectibles': ['collectible', 'figure', 'statue', 'memorabilia', 'signed'],
            'cards': ['card', 'pokemon', 'yugioh', 'magic', 'mtg', 'sports card', 'trading card'],
            'toys': ['toy', 'action figure', 'doll', 'lego', 'playset', 'game'],
            'home': ['furniture', 'decor', 'kitchen', 'bedding', 'lighting', 'rug'],
            'books': ['book', 'novel', 'textbook', 'magazine', 'comic'],
            'sports': ['sports', 'fitness', 'exercise', 'outdoor', 'camping'],
            'jewelry': ['jewelry', 'necklace', 'ring', 'bracelet', 'watch', 'earrings'],
            'automotive': ['car', 'auto', 'vehicle', 'motorcycle', 'parts']
        }

        for category, keywords in category_patterns.items():
            if any(keyword in text for keyword in keywords):
                return category

        return 'other'

    def extract_brand(self, title: str, description: str = "") -> Optional[str]:
        """
        Extract brand name from title or description

        Args:
            title: Item title
            description: Item description

        Returns:
            Brand name or None
        """
        text = title + " " + description

        # Common brand patterns
        common_brands = [
            'Nike', 'Adidas', 'Puma', 'Reebok', 'Under Armour',
            'Apple', 'Samsung', 'Sony', 'LG', 'Dell', 'HP',
            'Pokemon', 'Yu-Gi-Oh', 'Magic', 'MTG',
            'Lego', 'Hasbro', 'Mattel',
            'Gucci', 'Louis Vuitton', 'Prada', 'Coach',
            'Vintage', 'Retro'
        ]

        for brand in common_brands:
            if re.search(rf'\b{brand}\b', text, re.IGNORECASE):
                return brand

        return None

    def optimize_title(
        self,
        original_title: str,
        category: Optional[str] = None,
        brand: Optional[str] = None,
        condition: Optional[str] = None,
        max_length: int = 80,
        platform: str = 'generic'
    ) -> str:
        """
        Generate SEO-optimized title

        Args:
            original_title: Original title
            category: Item category
            brand: Brand name
            condition: Item condition
            max_length: Maximum title length
            platform: Target platform (affects length limits)

        Returns:
            Optimized title
        """
        # Platform-specific max lengths
        platform_max_lengths = {
            'ebay': 80,
            'poshmark': 50,
            'mercari': 40,
            'etsy': 140,
            'generic': 80
        }
        max_length = platform_max_lengths.get(platform, max_length)

        # Auto-detect category if not provided
        if not category:
            category = self.detect_category(original_title)

        # Auto-detect brand if not provided
        if not brand:
            brand = self.extract_brand(original_title)

        # Build optimized title
        parts = []

        # Add condition (if good/new)
        if condition and condition.lower() in ['new', 'like new', 'brand new']:
            condition_keywords = self.CONDITION_KEYWORDS.get(condition.lower(), [])
            if condition_keywords:
                parts.append(condition_keywords[0])

        # Add brand (high priority)
        if brand:
            parts.append(brand)

        # Add original title (cleaned)
        cleaned_title = re.sub(r'\s+', ' ', original_title).strip()
        parts.append(cleaned_title)

        # Add power word if space allows
        title = ' '.join(parts)
        if len(title) < max_length - 15:
            # Find a power word not already in title
            for word in self.POWER_WORDS:
                if word.lower() not in title.lower() and len(title) + len(word) + 1 <= max_length:
                    title = word + " " + title
                    break

        # Truncate if needed
        if len(title) > max_length:
            title = title[:max_length - 3] + '...'

        return title

    def enrich_description(
        self,
        original_description: str,
        title: str,
        category: Optional[str] = None,
        brand: Optional[str] = None,
        condition: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Enrich description with SEO keywords

        Args:
            original_description: Original description
            title: Item title
            category: Item category
            brand: Brand name
            condition: Item condition
            attributes: Additional item attributes

        Returns:
            Enriched description
        """
        # Auto-detect category if not provided
        if not category:
            category = self.detect_category(title, original_description)

        # Build enriched description
        enriched = original_description

        # Add category keywords if missing
        if category in self.CATEGORY_KEYWORDS:
            keywords = self.CATEGORY_KEYWORDS[category]
            for keyword in keywords[:3]:  # Add up to 3 relevant keywords
                if keyword.lower() not in enriched.lower():
                    enriched += f" {keyword}."

        # Add brand mention if missing
        if brand and brand.lower() not in enriched.lower():
            enriched = f"Authentic {brand}. " + enriched

        # Add condition details
        if condition:
            condition_lower = condition.lower()
            if condition_lower in self.CONDITION_KEYWORDS:
                condition_phrase = self.CONDITION_KEYWORDS[condition_lower][0]
                if condition_phrase.lower() not in enriched.lower():
                    enriched = f"Condition: {condition_phrase}. " + enriched

        # Add structured attributes
        if attributes:
            attr_text = "\n\nDetails:\n"
            for key, value in attributes.items():
                if value:
                    attr_text += f"• {key.title()}: {value}\n"
            enriched += attr_text

        return enriched.strip()

    def generate_keywords(
        self,
        title: str,
        description: str,
        category: Optional[str] = None,
        max_keywords: int = 20
    ) -> List[str]:
        """
        Generate SEO keywords from title and description

        Args:
            title: Item title
            description: Item description
            category: Item category
            max_keywords: Maximum number of keywords

        Returns:
            List of keywords
        """
        # Auto-detect category
        if not category:
            category = self.detect_category(title, description)

        keywords = set()

        # Extract words from title (high priority)
        title_words = re.findall(r'\b[A-Za-z]{3,}\b', title)
        keywords.update([w.lower() for w in title_words])

        # Extract words from description
        desc_words = re.findall(r'\b[A-Za-z]{4,}\b', description)
        keywords.update([w.lower() for w in desc_words[:30]])

        # Add category keywords
        if category in self.CATEGORY_KEYWORDS:
            keywords.update([k.lower() for k in self.CATEGORY_KEYWORDS[category]])

        # Remove common stop words
        stop_words = {
            'this', 'that', 'with', 'from', 'have', 'were', 'been',
            'their', 'what', 'which', 'when', 'where', 'will', 'just'
        }
        keywords = keywords - stop_words

        # Return top keywords (sorted by relevance - title words first)
        title_keywords = [k for k in keywords if k in title.lower()]
        other_keywords = [k for k in keywords if k not in title.lower()]

        return (title_keywords + other_keywords)[:max_keywords]

    def optimize_listing(
        self,
        listing: Dict[str, Any],
        platform: str = 'generic',
        use_ai: bool = False
    ) -> Dict[str, Any]:
        """
        Optimize entire listing for SEO

        Args:
            listing: Listing data (must have 'title', 'description')
            platform: Target platform
            use_ai: Use AI for advanced optimization (requires ai_client)

        Returns:
            Optimized listing data
        """
        optimized = listing.copy()

        # Extract current data
        title = listing.get('title', '')
        description = listing.get('description', '')
        category = listing.get('category')
        condition = listing.get('condition')
        attributes = listing.get('attributes', {})

        # Auto-detect brand
        brand = self.extract_brand(title, description)
        if not brand and isinstance(attributes, dict):
            brand = attributes.get('brand')

        # Optimize title
        optimized['title'] = self.optimize_title(
            original_title=title,
            category=category,
            brand=brand,
            condition=condition,
            platform=platform
        )

        # Enrich description
        optimized['description'] = self.enrich_description(
            original_description=description,
            title=title,
            category=category,
            brand=brand,
            condition=condition,
            attributes=attributes
        )

        # Generate keywords
        optimized['seo_keywords'] = self.generate_keywords(
            title=optimized['title'],
            description=optimized['description'],
            category=category
        )

        # AI enhancement (if available)
        if use_ai and self.ai_client:
            optimized = self._ai_enhance_listing(optimized)

        return optimized

    def _ai_enhance_listing(self, listing: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use AI to further enhance listing SEO (requires Claude/GPT API)

        Args:
            listing: Listing data

        Returns:
            AI-enhanced listing
        """
        # This would integrate with Claude API or other AI service
        # For now, return as-is
        return listing

    def sync_seo_across_platforms(
        self,
        listing_id: int,
        db,
        platforms: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Sync SEO-optimized content across all platforms

        Args:
            listing_id: Listing ID
            db: Database instance
            platforms: List of platforms to sync (None = all)

        Returns:
            Sync results
        """
        # Get listing
        listing = db.get_listing(listing_id)
        if not listing:
            return {'error': 'Listing not found'}

        results = {
            'listing_id': listing_id,
            'platforms_synced': [],
            'errors': []
        }

        # Get platform listings
        platform_listings = db.get_platform_listings(listing_id)

        for pl in platform_listings:
            platform = pl['platform']

            # Skip if not in target platforms
            if platforms and platform not in platforms:
                continue

            try:
                # Optimize for this platform
                optimized = self.optimize_listing(listing, platform=platform)

                # Update listing with optimized content
                db.update_listing(
                    listing_id=listing_id,
                    title=optimized['title'],
                    description=optimized['description']
                )

                results['platforms_synced'].append(platform)

            except Exception as e:
                results['errors'].append({
                    'platform': platform,
                    'error': str(e)
                })

        return results


def optimize_listing_seo(
    listing: Dict[str, Any],
    platform: str = 'generic'
) -> Dict[str, Any]:
    """
    Convenience function to optimize a single listing

    Args:
        listing: Listing data
        platform: Target platform

    Returns:
        Optimized listing
    """
    optimizer = SEOOptimizer()
    return optimizer.optimize_listing(listing, platform=platform)
