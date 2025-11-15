# AI Cross-Poster v2.0 - Feature Overview

## 🎉 NEW FEATURES IMPLEMENTED

### 1. ✅ Multi-Platform Listing & Syncing

**Location:** `src/sync/multi_platform_sync.py`

- **Post to multiple platforms simultaneously** using `MultiPlatformSyncManager`
- **Auto-cancel on other platforms when sold** - automatically removes listings from all platforms when one sells
- **Failed listing notifications** - get email alerts when posting fails
- **Automatic retry logic** - system retries failed posts up to 3 times
- **Sync tracking** - full audit log of all sync operations

**Usage:**
```python
from src.sync import MultiPlatformSyncManager

manager = MultiPlatformSyncManager.from_env()

# Post to all platforms
result = manager.post_to_all_platforms(listing, platforms=["ebay", "mercari"])

# Mark as sold (auto-cancels elsewhere)
manager.mark_sold(listing_id, sold_platform="ebay", sold_price=150.00)

# Retry failed posts
manager.retry_failed_posts()
```

### 2. ✅ Collectible Recognition & Database

**Location:** `src/collectibles/recognizer.py`

- **AI-powered collectible identification** using Claude (primary) + GPT-4 Vision (fallback)
- **Automatic pricing data** from market analysis
- **SQLite database** stores all identified collectibles for future reference
- **Confidence scoring** - know how certain the AI is
- **Market trend tracking** - increasing/stable/decreasing trends

**Collectibles Identified:**
- Trading cards (Pokemon, Sports, Magic, Yu-Gi-Oh)
- Action figures and toys
- Coins and currency
- Stamps
- Comic books
- Video games (sealed, rare, retro)
- Vintage clothing/streetwear
- Vinyl records
- Movie/sports memorabilia
- Limited edition sneakers
- Designer items
- Collectible books

**Usage:**
```python
from src.collectibles import identify_collectible

# Analyze photos to identify collectible
is_collectible, collectible_id, analysis = identify_collectible(photos)

if is_collectible:
    print(f"Found: {analysis['name']}")
    print(f"Value: ${analysis['estimated_value_low']} - ${analysis['estimated_value_high']}")
    print(f"Stored in database as ID: {collectible_id}")
```

### 3. ✅ Detailed Attribute Detection

**Location:** `src/collectibles/attribute_detector.py`

- **Item type detection** (shirt, pants, socks, shoes, etc.)
- **Size detection** (S/M/L/XL, numeric sizes, measurements)
- **Color identification** (primary, secondary, patterns)
- **Material analysis** (cotton, polyester, leather, etc.)
- **Condition assessment** (new, excellent, good, fair, poor)
- **Brand and model** identification
- **Style classification** (casual, formal, athletic, vintage, etc.)

**Usage:**
```python
from src.collectibles import detect_attributes

attributes = detect_attributes(photos)

print(f"Type: {attributes['item_type']['specific_type']}")
print(f"Size: {attributes['size']['size']}")
print(f"Color: {attributes['color']['primary']}")
print(f"Brand: {attributes['brand']['name']}")
print(f"Condition: {attributes['condition']['overall']}")
```

### 4. ✅ Dual AI Setup (Already Implemented!)

**Location:** `src/enhancer/ai_enhancer.py`

- **Claude as primary** (cost-efficient, ~90% success rate)
- **GPT-4 Vision as fallback** (only used when Claude can't identify)
- **Cost savings** - avoid double analysis on every item

This was already working in v1.0 and carries over!

### 5. ✅ Shopping Mode & Database Lookup

**Location:** `src/shopping/lookup.py`

- **Quick lookup** by name/brand while shopping
- **Profit calculator** - know if a purchase will be profitable
- **Price comparison** - compare asking price vs market value
- **Mobile-friendly** - use database on the go

**Usage:**
```python
from src.shopping import quick_lookup, profit_calculator, compare_prices

# Quick lookup while shopping
results = quick_lookup("Pokemon Charizard")

# Calculate profit
profit = profit_calculator(
    collectible_id=123,
    purchase_price=50.00,
    fees_percentage=15.0
)
print(f"Expected profit: ${profit['expected_profit']:.2f}")
print(f"ROI: {profit['expected_roi']:.0f}%")

# Compare prices
comparison = compare_prices("Vintage Nike Jacket", asking_price=45.00)
print(f"Recommendation: {comparison['recommendation']}")
```

### 6. ✅ Email Alerts & Notifications

**Location:** `src/notifications/notification_manager.py`

**Email notifications for:**
- **Sales** - with shipping label attachment
- **Offers** - when someone makes an offer
- **Listing failures** - when posting fails
- **Price alerts** - when collectibles hit target price

**In-app notifications:**
- Stored in database
- Unread count tracking
- Full notification history

**Usage:**
```python
from src.notifications import NotificationManager

notifier = NotificationManager.from_env()

# Send sale notification (with shipping label)
notifier.send_sale_notification(
    listing_id=123,
    platform="eBay",
    sale_price=150.00,
    buyer_email="buyer@example.com",
    tracking_number="1Z999AA10123456784",
    shipping_label_path="./labels/label_123.pdf",
    listing_title="Nike Air Jordan 1"
)

# Get unread notifications
unread = notifier.get_unread_count()
```

### 7. ✅ Database System

**Location:** `src/database/db.py`

**Tables:**
- `collectibles` - All identified collectibles with pricing data
- `listings` - Your listings
- `platform_listings` - Track where each listing is posted
- `sync_log` - Full audit log of sync operations
- `notifications` - In-app notifications
- `price_alerts` - Collectibles you're watching

**Usage:**
```python
from src.database import get_db

db = get_db()

# Search collectibles
results = db.search_collectibles(
    query="Pokemon",
    min_value=100.00,
    category="trading_cards"
)

# Get listing info
listing = db.get_listing(listing_id)

# Get platform status
platform_listings = db.get_platform_listings(listing_id)
```

---

## 📁 NEW FILE STRUCTURE

```
ai-cross-poster/
├── src/
│   ├── __init__.py (updated with new modules)
│   ├── database/
│   │   ├── __init__.py
│   │   └── db.py (SQLite database handler)
│   ├── collectibles/
│   │   ├── __init__.py
│   │   ├── recognizer.py (collectible AI recognition)
│   │   └── attribute_detector.py (detailed attribute detection)
│   ├── sync/
│   │   ├── __init__.py
│   │   └── multi_platform_sync.py (multi-platform posting & sync)
│   ├── notifications/
│   │   ├── __init__.py
│   │   └── notification_manager.py (email alerts & notifications)
│   └── shopping/
│       ├── __init__.py
│       └── lookup.py (shopping mode & database lookup)
├── data/
│   └── cross_poster.db (auto-created SQLite database)
└── FEATURES.md (this file)
```

---

## 🚀 QUICK START EXAMPLES

### Example 1: Post to All Platforms with Collectible Recognition

```python
from src.schema import UnifiedListing, Photo, Price, ListingCondition
from src.collectibles import identify_collectible
from src.sync import MultiPlatformSyncManager

# Load photos
photos = [
    Photo(local_path="./images/card_front.jpg", is_primary=True),
    Photo(local_path="./images/card_back.jpg"),
]

# Check if it's a collectible
is_collectible, collectible_id, analysis = identify_collectible(photos)

if is_collectible:
    print(f"✅ Collectible: {analysis['name']}")
    print(f"   Value: ${analysis['estimated_value_low']}-${analysis['estimated_value_high']}")

    # Create listing
    listing = UnifiedListing(
        title=analysis['name'],
        description=analysis.get('description', 'AI generated description'),
        price=Price(amount=analysis['estimated_value_avg']),
        condition=ListingCondition.EXCELLENT,
        photos=photos,
    )

    # Post to all platforms
    manager = MultiPlatformSyncManager.from_env()
    result = manager.post_to_all_platforms(
        listing,
        platforms=["ebay", "mercari"],
        collectible_id=collectible_id,
        cost=50.00  # What you paid
    )

    print(f"✅ Posted to {result['success_count']} platforms")
```

### Example 2: Shopping Mode - Should I Buy This?

```python
from src.shopping import quick_lookup, profit_calculator

# Quick lookup while at a yard sale
results = quick_lookup("Vintage Nintendo Game Boy")

if results:
    collectible_id = results[0]['id']

    # Calculate if it's profitable
    profit = profit_calculator(
        collectible_id=collectible_id,
        purchase_price=30.00,  # They're asking $30
        fees_percentage=15.0
    )

    if profit['is_profitable']:
        print(f"✅ BUY IT! Expected profit: ${profit['expected_profit']:.2f}")
        print(f"   ROI: {profit['expected_roi']:.0f}%")
    else:
        print(f"❌ PASS - Not profitable")
```

### Example 3: Mark Item Sold (Auto-Cancels Everywhere)

```python
from src.sync import mark_sold

# Item sold on eBay for $150
result = mark_sold(
    listing_id=123,
    sold_platform="ebay",
    sold_price=150.00
)

# Automatically:
# ✅ Marks as sold in database
# ✅ Cancels on Mercari
# ✅ Sends email notification with shipping label
# ✅ Logs sync operation

print(f"Canceled on: {', '.join(result['canceled_platforms'])}")
```

---

## 📧 EMAIL CONFIGURATION

Add to your `.env` file:

```bash
# Email Notifications
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password  # For Gmail, use App Password
NOTIFICATION_FROM_EMAIL=your_email@gmail.com
NOTIFICATION_TO_EMAIL=your_email@gmail.com
```

---

## 🎯 NEXT STEPS FOR INTEGRATION

The system is ready to use! To integrate into the main menu:

1. **Import new modules** in `main.py`:
   ```python
   from src.collectibles import identify_collectible, detect_attributes
   from src.sync import MultiPlatformSyncManager
   from src.shopping import quick_lookup, profit_calculator
   from src.notifications import NotificationManager
   from src.database import get_db
   ```

2. **Add menu options**:
   - "Identify Collectible from Photos"
   - "Shopping Mode (Lookup & Profit Calculator)"
   - "Mark Item as Sold"
   - "View Notifications"
   - "Retry Failed Posts"

3. **Replace simple publish with sync manager** for multi-platform posting

---

## 🧪 TESTING

Test imports:
```bash
python3 -c "from src.database import get_db; from src.collectibles import identify_collectible; from src.sync import MultiPlatformSyncManager; print('✅ All imports successful')"
```

---

## 📊 DATABASE LOCATION

Database auto-creates at: `./data/cross_poster.db`

View with SQLite browser or:
```bash
sqlite3 data/cross_poster.db
.tables
.schema collectibles
SELECT * FROM collectibles LIMIT 5;
```

---

**Built with ❤️ for resellers everywhere**
