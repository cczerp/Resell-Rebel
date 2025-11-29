"""
CSV Import System for AI Cross-Poster
Supports importing from any marketplace CSV format and normalizing to unified schema
"""

import csv
import json
import re
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from datetime import datetime
import uuid


class CSVImporter:
    """Import and normalize CSV data from various marketplaces"""

    # Platform-specific CSV field mappings
    PLATFORM_MAPPINGS = {
        'ebay': {
            'title': ['Title', 'Item Title', 'title'],
            'description': ['Description', 'Item Description', 'description'],
            'price': ['Price', 'Start Price', 'Buy It Now Price', 'price'],
            'cost': ['Cost', 'Purchase Price', 'cost'],
            'condition': ['Condition', 'Item Condition', 'condition'],
            'category': ['Category', 'Primary Category', 'category'],
            'sku': ['SKU', 'Custom Label', 'sku'],
            'upc': ['UPC', 'EAN', 'ISBN', 'Product ID', 'upc'],
            'quantity': ['Quantity', 'Available Qty', 'quantity'],
            'photos': ['Photo URL', 'PicURL', 'Image', 'photos'],
            'storage_location': ['Location', 'Storage Location', 'location'],
        },
        'poshmark': {
            'title': ['Title', 'Item Name'],
            'description': ['Description', 'Item Description'],
            'price': ['Price', 'Listed Price'],
            'condition': ['Condition'],
            'category': ['Category', 'Department'],
            'brand': ['Brand'],
            'size': ['Size'],
            'color': ['Color'],
            'photos': ['Photo1', 'Photo2', 'Photo3', 'Photo4'],
        },
        'mercari': {
            'title': ['name', 'title', 'Name', 'Title'],
            'description': ['description', 'Description'],
            'price': ['price', 'Price'],
            'condition': ['condition', 'Condition'],
            'category': ['category', 'Category'],
            'brand': ['brand', 'Brand'],
            'photos': ['photo_url', 'image', 'Photo'],
        },
        'generic': {
            'title': ['title', 'Title', 'name', 'Name', 'Item Name'],
            'description': ['description', 'Description', 'details', 'Details'],
            'price': ['price', 'Price', 'amount', 'Amount'],
            'cost': ['cost', 'Cost', 'purchase_price', 'Purchase Price'],
            'condition': ['condition', 'Condition'],
            'category': ['category', 'Category', 'type', 'Type'],
            'sku': ['sku', 'SKU', 'item_id', 'Item ID'],
            'upc': ['upc', 'UPC', 'barcode', 'Barcode'],
            'quantity': ['quantity', 'Quantity', 'qty', 'Qty'],
            'storage_location': ['location', 'Location', 'storage', 'Storage'],
        }
    }

    def __init__(self, user_id: int, db=None):
        """
        Initialize CSV Importer

        Args:
            user_id: User ID for ownership tracking
            db: Database instance (optional, for duplicate detection)
        """
        self.user_id = user_id
        self.db = db
        self.auto_sku_counter = 1

    def detect_platform(self, headers: List[str]) -> str:
        """
        Auto-detect CSV platform based on headers

        Args:
            headers: CSV column headers

        Returns:
            Platform name ('ebay', 'poshmark', 'mercari', or 'generic')
        """
        headers_lower = [h.lower() for h in headers]

        # eBay detection
        if any(h in headers_lower for h in ['customlabel', 'startprice', 'picurl']):
            return 'ebay'

        # Poshmark detection
        if 'department' in headers_lower or 'posh' in ''.join(headers_lower):
            return 'poshmark'

        # Mercari detection
        if 'mercari' in ''.join(headers_lower):
            return 'mercari'

        return 'generic'

    def find_field_value(self, row: Dict[str, str], field_names: List[str]) -> Optional[str]:
        """
        Find value for a field from possible column names

        Args:
            row: CSV row data
            field_names: List of possible column names for this field

        Returns:
            Field value or None
        """
        for field_name in field_names:
            # Try exact match
            if field_name in row and row[field_name]:
                return row[field_name].strip()

            # Try case-insensitive match
            for key in row.keys():
                if key.lower() == field_name.lower() and row[key]:
                    return row[key].strip()

        return None

    def normalize_price(self, price_str: Optional[str]) -> Optional[float]:
        """
        Normalize price string to float

        Args:
            price_str: Price string (e.g., "$19.99", "19,99", "19.99 USD")

        Returns:
            Float price or None
        """
        if not price_str:
            return None

        # Remove currency symbols and whitespace
        cleaned = re.sub(r'[^\d.,]', '', price_str)

        # Handle European format (comma as decimal)
        if ',' in cleaned and '.' not in cleaned:
            cleaned = cleaned.replace(',', '.')
        elif ',' in cleaned and '.' in cleaned:
            # Assume comma is thousands separator
            cleaned = cleaned.replace(',', '')

        try:
            return float(cleaned)
        except ValueError:
            return None

    def normalize_photos(self, row: Dict[str, str], platform: str) -> List[str]:
        """
        Extract and normalize photo URLs from row

        Args:
            row: CSV row data
            platform: Platform name

        Returns:
            List of photo URLs
        """
        photos = []

        # Try platform-specific photo fields
        if platform in self.PLATFORM_MAPPINGS:
            photo_fields = self.PLATFORM_MAPPINGS[platform].get('photos', [])
            for field in photo_fields:
                value = self.find_field_value(row, [field])
                if value:
                    # Split by common separators
                    urls = re.split(r'[,;|]', value)
                    photos.extend([url.strip() for url in urls if url.strip()])

        # Also check for numbered photo columns (Photo1, Photo2, etc.)
        for key in row.keys():
            if re.match(r'photo\d+', key.lower()) and row[key]:
                photos.append(row[key].strip())

        return list(dict.fromkeys(photos))  # Remove duplicates while preserving order

    def generate_sku(self, category: Optional[str] = None) -> str:
        """
        Auto-generate SKU

        Args:
            category: Item category (optional, for prefix)

        Returns:
            Generated SKU
        """
        prefix = ""
        if category:
            # Use first 3 letters of category
            prefix = re.sub(r'[^A-Za-z]', '', category)[:3].upper() + "-"

        sku = f"{prefix}AUTO-{self.auto_sku_counter:06d}"
        self.auto_sku_counter += 1
        return sku

    def check_duplicate(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Check if item already exists in database

        Args:
            item: Normalized item data

        Returns:
            Existing item or None
        """
        if not self.db:
            return None

        # Check by SKU
        if item.get('sku'):
            existing = self.db.get_listing_by_sku(item['sku'])
            if existing:
                return existing

        # Check by UPC
        if item.get('upc'):
            existing = self.db.get_listing_by_upc(item['upc'])
            if existing:
                return existing

        # Check by title similarity (fuzzy match)
        if item.get('title'):
            existing = self.db.search_listings_by_title(
                self.user_id,
                item['title'][:50],
                threshold=0.8
            )
            if existing:
                return existing[0]

        return None

    def normalize_row(self, row: Dict[str, str], platform: str) -> Dict[str, Any]:
        """
        Normalize CSV row to unified listing format

        Args:
            row: CSV row data
            platform: Platform name

        Returns:
            Normalized item data
        """
        mapping = self.PLATFORM_MAPPINGS.get(platform, self.PLATFORM_MAPPINGS['generic'])

        # Extract basic fields
        title = self.find_field_value(row, mapping.get('title', []))
        description = self.find_field_value(row, mapping.get('description', []))
        price_str = self.find_field_value(row, mapping.get('price', []))
        cost_str = self.find_field_value(row, mapping.get('cost', []))
        condition = self.find_field_value(row, mapping.get('condition', []))
        category = self.find_field_value(row, mapping.get('category', []))
        sku = self.find_field_value(row, mapping.get('sku', []))
        upc = self.find_field_value(row, mapping.get('upc', []))
        quantity_str = self.find_field_value(row, mapping.get('quantity', []))
        storage_location = self.find_field_value(row, mapping.get('storage_location', []))

        # Normalize prices
        price = self.normalize_price(price_str)
        cost = self.normalize_price(cost_str)

        # Normalize quantity
        quantity = 1
        if quantity_str:
            try:
                quantity = int(re.sub(r'[^\d]', '', quantity_str))
            except ValueError:
                quantity = 1

        # Auto-generate SKU if missing
        if not sku:
            sku = self.generate_sku(category)

        # Extract photos
        photos = self.normalize_photos(row, platform)

        # Extract additional attributes (brand, size, color, etc.)
        attributes = {}
        for key, value in row.items():
            if key.lower() in ['brand', 'size', 'color', 'material', 'style']:
                if value and value.strip():
                    attributes[key.lower()] = value.strip()

        # Create normalized item
        normalized = {
            'listing_uuid': str(uuid.uuid4()),
            'user_id': self.user_id,
            'title': title or 'Untitled Item',
            'description': description or '',
            'price': price or 0.0,
            'cost': cost,
            'condition': condition or 'Used',
            'category': category,
            'item_type': category,
            'attributes': attributes,
            'photos': photos,
            'quantity': quantity,
            'storage_location': storage_location,
            'sku': sku,
            'upc': upc,
            'status': 'draft',  # Default to draft mode
            'import_source': platform,
            'import_date': datetime.now().isoformat(),
        }

        return normalized

    def import_csv(
        self,
        csv_path: str,
        platform: Optional[str] = None,
        auto_publish: bool = False,
        skip_duplicates: bool = True
    ) -> Dict[str, Any]:
        """
        Import CSV file and normalize all rows

        Args:
            csv_path: Path to CSV file
            platform: Platform name (auto-detected if None)
            auto_publish: If True, set status to 'active' instead of 'draft'
            skip_duplicates: If True, skip items that already exist

        Returns:
            Import results with stats
        """
        csv_file = Path(csv_path)
        if not csv_file.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        results = {
            'total_rows': 0,
            'imported': 0,
            'skipped_duplicates': 0,
            'errors': 0,
            'items': [],
            'duplicates': [],
            'error_details': []
        }

        # Read CSV
        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames or []

            # Auto-detect platform if not specified
            if not platform:
                platform = self.detect_platform(headers)

            print(f"📁 Importing CSV from {platform} with {len(headers)} columns")

            for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
                results['total_rows'] += 1

                try:
                    # Normalize row
                    normalized_item = self.normalize_row(row, platform)

                    # Check for duplicates
                    if skip_duplicates:
                        duplicate = self.check_duplicate(normalized_item)
                        if duplicate:
                            results['skipped_duplicates'] += 1
                            results['duplicates'].append({
                                'row': row_num,
                                'title': normalized_item['title'],
                                'existing_id': duplicate.get('id')
                            })
                            continue

                    # Override status if auto-publish
                    if auto_publish:
                        normalized_item['status'] = 'active'

                    results['imported'] += 1
                    results['items'].append(normalized_item)

                except Exception as e:
                    results['errors'] += 1
                    results['error_details'].append({
                        'row': row_num,
                        'error': str(e)
                    })

        print(f"✅ CSV Import Complete:")
        print(f"   Total Rows: {results['total_rows']}")
        print(f"   Imported: {results['imported']}")
        print(f"   Skipped (Duplicates): {results['skipped_duplicates']}")
        print(f"   Errors: {results['errors']}")

        return results

    def save_to_database(self, import_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save imported items to database

        Args:
            import_results: Results from import_csv()

        Returns:
            Save results with IDs
        """
        if not self.db:
            raise ValueError("Database instance required to save items")

        save_results = {
            'saved': 0,
            'failed': 0,
            'listing_ids': [],
            'errors': []
        }

        for item in import_results['items']:
            try:
                listing_id = self.db.create_listing(
                    listing_uuid=item['listing_uuid'],
                    user_id=item['user_id'],
                    title=item['title'],
                    description=item['description'],
                    price=item['price'],
                    cost=item.get('cost'),
                    condition=item['condition'],
                    category=item.get('category'),
                    item_type=item.get('item_type'),
                    attributes=item.get('attributes'),
                    photos=item['photos'],
                    quantity=item['quantity'],
                    storage_location=item.get('storage_location'),
                    sku=item.get('sku'),
                    upc=item.get('upc'),
                    status=item['status']
                )

                save_results['saved'] += 1
                save_results['listing_ids'].append(listing_id)

            except Exception as e:
                save_results['failed'] += 1
                save_results['errors'].append({
                    'title': item['title'],
                    'error': str(e)
                })

        print(f"💾 Database Save Complete:")
        print(f"   Saved: {save_results['saved']}")
        print(f"   Failed: {save_results['failed']}")

        return save_results


def import_and_save_csv(
    csv_path: str,
    user_id: int,
    db,
    platform: Optional[str] = None,
    auto_publish: bool = False,
    skip_duplicates: bool = True
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Convenience function to import CSV and save to database in one step

    Args:
        csv_path: Path to CSV file
        user_id: User ID
        db: Database instance
        platform: Platform name (auto-detected if None)
        auto_publish: If True, items go to 'active' instead of 'draft'
        skip_duplicates: If True, skip items that already exist

    Returns:
        Tuple of (import_results, save_results)
    """
    importer = CSVImporter(user_id=user_id, db=db)

    # Import CSV
    import_results = importer.import_csv(
        csv_path=csv_path,
        platform=platform,
        auto_publish=auto_publish,
        skip_duplicates=skip_duplicates
    )

    # Save to database
    save_results = importer.save_to_database(import_results)

    return import_results, save_results
