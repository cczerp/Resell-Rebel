"""
AI Cross-Poster
===============
Analyzes images to create optimized listings on multiple resell platforms.

Main components:
- schema: Unified listing schema
- adapters: Platform-specific adapters (eBay, Mercari)
- enhancer: AI-powered listing enhancement
- publisher: Cross-platform publishing orchestrator
- collectibles: Collectible recognition and attribute detection
- database: SQLite database for collectibles and listings
- sync: Multi-platform synchronization and auto-cancellation
- notifications: Email alerts for sales, offers, and failures
- shopping: Database lookup for shopping mode
"""

from .schema import (
    UnifiedListing,
    Photo,
    Price,
    Shipping,
    Category,
    ItemSpecifics,
    SEOData,
    ListingCondition,
    ListingFormat,
)

from .adapters import (
    EbayAdapter,
    MercariAdapter,
)

from .enhancer import (
    AIEnhancer,
    enhance_listing,
)

from .publisher import (
    CrossPlatformPublisher,
    PublishResult,
    publish_to_ebay,
    publish_to_mercari,
    publish_to_all,
)

from .collectibles import (
    CollectibleRecognizer,
    identify_collectible,
    AttributeDetector,
    detect_attributes,
)

from .database import (
    Database,
    get_db,
)

from .sync import (
    MultiPlatformSyncManager,
)

from .notifications import (
    NotificationManager,
)

from .shopping import (
    ShoppingLookup,
    quick_lookup,
    profit_calculator,
    compare_prices,
)

__version__ = "2.0.0"  # Major update with collectibles and sync features

__all__ = [
    # Schema
    "UnifiedListing",
    "Photo",
    "Price",
    "Shipping",
    "Category",
    "ItemSpecifics",
    "SEOData",
    "ListingCondition",
    "ListingFormat",
    # Adapters
    "EbayAdapter",
    "MercariAdapter",
    # Enhancer
    "AIEnhancer",
    "enhance_listing",
    # Publisher
    "CrossPlatformPublisher",
    "PublishResult",
    "publish_to_ebay",
    "publish_to_mercari",
    "publish_to_all",
    # Collectibles
    "CollectibleRecognizer",
    "identify_collectible",
    "AttributeDetector",
    "detect_attributes",
    # Database
    "Database",
    "get_db",
    # Sync
    "MultiPlatformSyncManager",
    # Notifications
    "NotificationManager",
    # Shopping
    "ShoppingLookup",
    "quick_lookup",
    "profit_calculator",
    "compare_prices",
]
