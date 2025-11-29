"""
Item Lifecycle Automation for AI Cross-Poster
Handles auto-delisting, status synchronization, and archiving
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import time


class ItemLifecycleManager:
    """Manage item lifecycle across platforms"""

    def __init__(self, db):
        """
        Initialize Lifecycle Manager

        Args:
            db: Database instance
        """
        self.db = db

    def mark_item_sold(
        self,
        listing_id: int,
        platform: str,
        sold_price: Optional[float] = None,
        buyer_info: Optional[Dict[str, str]] = None,
        auto_delist: bool = True,
        delist_delay_minutes: int = 15
    ) -> Dict[str, Any]:
        """
        Mark item as sold and optionally delist from other platforms

        Args:
            listing_id: Listing ID
            platform: Platform where item sold
            sold_price: Sale price
            buyer_info: Buyer information
            auto_delist: Automatically delist from other platforms
            delist_delay_minutes: Delay before delisting (default 15 min)

        Returns:
            Operation results
        """
        # Get listing
        listing = self.db.get_listing(listing_id)
        if not listing:
            return {'success': False, 'error': 'Listing not found'}

        # Mark as sold in database
        self.db.mark_listing_sold(
            listing_id=listing_id,
            platform=platform,
            sold_price=sold_price
        )

        # Create notification
        self.db.create_notification(
            type='sale',
            title=f'Item Sold on {platform}!',
            message=f'{listing["title"]} sold for ${sold_price or listing["price"]:.2f}',
            listing_id=listing_id,
            platform=platform,
            data={
                'buyer': buyer_info,
                'sold_price': sold_price,
                'platform': platform
            }
        )

        results = {
            'success': True,
            'listing_id': listing_id,
            'sold_platform': platform,
            'sold_price': sold_price,
            'delisted_platforms': [],
            'scheduled_delistings': []
        }

        # Auto-delist from other platforms
        if auto_delist:
            # Get all platform listings
            platform_listings = self.db.get_platform_listings(listing_id)

            for pl in platform_listings:
                pl_platform = pl['platform']
                pl_status = pl['status']

                # Skip the platform where it sold
                if pl_platform == platform:
                    continue

                # Skip if already delisted
                if pl_status in ['canceled', 'sold', 'delisted']:
                    continue

                if delist_delay_minutes > 0:
                    # Schedule delayed delisting
                    cancel_time = datetime.now() + timedelta(minutes=delist_delay_minutes)

                    cursor = self.db._get_cursor()
                    cursor.execute("""
                        UPDATE platform_listings
                        SET cancel_scheduled_at = %s
                        WHERE listing_id = %s AND platform = %s
                    """, (cancel_time, listing_id, pl_platform))
                    self.db.conn.commit()

                    results['scheduled_delistings'].append({
                        'platform': pl_platform,
                        'scheduled_time': cancel_time.isoformat()
                    })

                else:
                    # Immediate delisting
                    self._delist_from_platform(listing_id, pl_platform)
                    results['delisted_platforms'].append(pl_platform)

        return results

    def _delist_from_platform(self, listing_id: int, platform: str) -> bool:
        """
        Delist item from a specific platform

        Args:
            listing_id: Listing ID
            platform: Platform name

        Returns:
            Success status
        """
        try:
            # Update platform listing status
            self.db.update_platform_listing_status(
                listing_id=listing_id,
                platform=platform,
                status='canceled'
            )

            # Log the action
            self.db.log_sync(
                listing_id=listing_id,
                platform=platform,
                action='delist',
                status='success',
                details={'reason': 'sold_on_other_platform', 'auto_delisted': True}
            )

            # TODO: Call platform API to actually delist
            # This would use the platform adapters to make API calls

            return True

        except Exception as e:
            self.db.log_sync(
                listing_id=listing_id,
                platform=platform,
                action='delist',
                status='failed',
                details={'error': str(e)}
            )
            return False

    def process_scheduled_delistings(self) -> Dict[str, Any]:
        """
        Process all scheduled delistings that are due

        Returns:
            Processing results
        """
        cursor = self.db._get_cursor()

        # Find all platform listings with scheduled delistings
        cursor.execute("""
            SELECT listing_id, platform, cancel_scheduled_at
            FROM platform_listings
            WHERE cancel_scheduled_at IS NOT NULL
            AND cancel_scheduled_at <= %s
            AND status IN ('active', 'pending')
        """, (datetime.now(),))

        scheduled = [dict(row) for row in cursor.fetchall()]

        results = {
            'processed': 0,
            'succeeded': 0,
            'failed': 0,
            'details': []
        }

        for item in scheduled:
            listing_id = item['listing_id']
            platform = item['platform']

            results['processed'] += 1

            # Delist
            success = self._delist_from_platform(listing_id, platform)

            if success:
                results['succeeded'] += 1

                # Clear the scheduled time
                cursor.execute("""
                    UPDATE platform_listings
                    SET cancel_scheduled_at = NULL
                    WHERE listing_id = %s AND platform = %s
                """, (listing_id, platform))
                self.db.conn.commit()

                results['details'].append({
                    'listing_id': listing_id,
                    'platform': platform,
                    'status': 'success'
                })
            else:
                results['failed'] += 1
                results['details'].append({
                    'listing_id': listing_id,
                    'platform': platform,
                    'status': 'failed'
                })

        return results

    def archive_sold_items(
        self,
        days_since_sale: int = 30,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Archive sold items after a certain period

        Args:
            days_since_sale: Number of days since sale
            user_id: User ID (optional, archives for all users if None)

        Returns:
            Archive results
        """
        cursor = self.db._get_cursor()

        # Find sold items older than threshold
        cutoff_date = datetime.now() - timedelta(days=days_since_sale)

        query = """
            SELECT id FROM listings
            WHERE status = 'sold'
            AND sold_date <= %s
        """
        params = [cutoff_date]

        if user_id:
            query += " AND user_id::text = %s::text"
            params.append(str(user_id))

        cursor.execute(query, params)
        listings_to_archive = [dict(row)['id'] for row in cursor.fetchall()]

        results = {
            'archived': 0,
            'failed': 0,
            'listing_ids': []
        }

        for listing_id in listings_to_archive:
            try:
                # Update status to archived
                cursor.execute("""
                    UPDATE listings
                    SET status = 'archived', updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (listing_id,))
                self.db.conn.commit()

                results['archived'] += 1
                results['listing_ids'].append(listing_id)

            except Exception as e:
                results['failed'] += 1

        return results

    def sync_item_status_across_platforms(
        self,
        listing_id: int,
        new_status: str,
        exclude_platforms: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Sync item status across all platforms

        Args:
            listing_id: Listing ID
            new_status: New status to set
            exclude_platforms: Platforms to exclude from sync

        Returns:
            Sync results
        """
        exclude_platforms = exclude_platforms or []

        # Get all platform listings
        platform_listings = self.db.get_platform_listings(listing_id)

        results = {
            'success': True,
            'synced_platforms': [],
            'failed_platforms': [],
            'skipped_platforms': exclude_platforms
        }

        for pl in platform_listings:
            platform = pl['platform']

            if platform in exclude_platforms:
                continue

            try:
                # Update status
                self.db.update_platform_listing_status(
                    listing_id=listing_id,
                    platform=platform,
                    status=new_status
                )

                results['synced_platforms'].append(platform)

            except Exception as e:
                results['failed_platforms'].append({
                    'platform': platform,
                    'error': str(e)
                })
                results['success'] = False

        return results

    def handle_sale_notification(
        self,
        platform: str,
        platform_listing_id: str,
        sold_price: float,
        buyer_info: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Handle incoming sale notification from platform

        Args:
            platform: Platform name
            platform_listing_id: Platform's listing ID
            sold_price: Sale price
            buyer_info: Buyer information

        Returns:
            Handling results
        """
        cursor = self.db._get_cursor()

        # Find listing by platform listing ID
        cursor.execute("""
            SELECT listing_id FROM platform_listings
            WHERE platform = %s AND platform_listing_id = %s
        """, (platform, platform_listing_id))

        result = cursor.fetchone()
        if not result:
            return {
                'success': False,
                'error': 'Listing not found',
                'platform': platform,
                'platform_listing_id': platform_listing_id
            }

        listing_id = result['listing_id']

        # Mark as sold and auto-delist
        return self.mark_item_sold(
            listing_id=listing_id,
            platform=platform,
            sold_price=sold_price,
            buyer_info=buyer_info,
            auto_delist=True,
            delist_delay_minutes=15
        )

    def get_storage_location_on_sale(self, listing_id: int) -> Optional[str]:
        """
        Get storage location when item sells (for fulfillment)

        Args:
            listing_id: Listing ID

        Returns:
            Storage location or None
        """
        listing = self.db.get_listing(listing_id)
        if not listing:
            return None

        return listing.get('storage_location')


def mark_sold_and_delist(
    listing_id: int,
    platform: str,
    sold_price: float,
    db,
    delay_minutes: int = 15
) -> Dict[str, Any]:
    """
    Convenience function to mark item sold and auto-delist

    Args:
        listing_id: Listing ID
        platform: Platform where sold
        sold_price: Sale price
        db: Database instance
        delay_minutes: Delay before delisting

    Returns:
        Results
    """
    manager = ItemLifecycleManager(db)
    return manager.mark_item_sold(
        listing_id=listing_id,
        platform=platform,
        sold_price=sold_price,
        auto_delist=True,
        delist_delay_minutes=delay_minutes
    )
