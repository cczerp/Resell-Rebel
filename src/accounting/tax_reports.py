"""
Tax & Accounting Reporting System for AI Cross-Poster
Tracks profit, COGS, platform fees, and generates tax reports
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
import json


class TaxReportGenerator:
    """Generate tax and accounting reports for sellers"""

    # Platform fee structures (approximate percentages)
    PLATFORM_FEES = {
        'ebay': {
            'final_value_fee': 12.9,  # 12.9% for most categories
            'payment_processing': 2.9,  # 2.9% + $0.30
            'payment_processing_fixed': 0.30
        },
        'poshmark': {
            'final_value_fee': 20.0,  # 20% on sales over $15
            'under_15_fee': 2.95  # Flat $2.95 on sales under $15
        },
        'mercari': {
            'final_value_fee': 10.0,  # 10% selling fee
            'payment_processing': 2.9,
            'payment_processing_fixed': 0.30
        },
        'etsy': {
            'listing_fee': 0.20,
            'final_value_fee': 6.5,  # 6.5% transaction fee
            'payment_processing': 3.0,
            'payment_processing_fixed': 0.25
        },
        'mercari_shops': {
            'final_value_fee': 5.0,  # 5% for Shops
            'payment_processing': 2.9,
            'payment_processing_fixed': 0.30
        },
        'generic': {
            'final_value_fee': 10.0,
            'payment_processing': 2.9,
            'payment_processing_fixed': 0.30
        }
    }

    def __init__(self, db):
        """
        Initialize Tax Report Generator

        Args:
            db: Database instance
        """
        self.db = db

    def calculate_platform_fees(
        self,
        platform: str,
        sold_price: float,
        listing_count: int = 1
    ) -> Dict[str, float]:
        """
        Calculate platform fees for a sale

        Args:
            platform: Platform name
            sold_price: Sale price
            listing_count: Number of listings (for Etsy listing fees)

        Returns:
            Dictionary of fee breakdown
        """
        fees = self.PLATFORM_FEES.get(platform, self.PLATFORM_FEES['generic'])
        breakdown = {
            'final_value_fee': 0.0,
            'payment_processing_fee': 0.0,
            'listing_fee': 0.0,
            'total_fees': 0.0
        }

        # Poshmark special case
        if platform == 'poshmark':
            if sold_price < 15:
                breakdown['final_value_fee'] = fees['under_15_fee']
            else:
                breakdown['final_value_fee'] = sold_price * (fees['final_value_fee'] / 100)
        else:
            # Standard percentage fee
            breakdown['final_value_fee'] = sold_price * (fees.get('final_value_fee', 0) / 100)

        # Payment processing fee
        if 'payment_processing' in fees:
            breakdown['payment_processing_fee'] = (
                sold_price * (fees['payment_processing'] / 100) +
                fees.get('payment_processing_fixed', 0)
            )

        # Listing fee (Etsy)
        if 'listing_fee' in fees:
            breakdown['listing_fee'] = fees['listing_fee'] * listing_count

        # Total
        breakdown['total_fees'] = (
            breakdown['final_value_fee'] +
            breakdown['payment_processing_fee'] +
            breakdown['listing_fee']
        )

        return breakdown

    def calculate_profit(
        self,
        sold_price: float,
        cost: Optional[float],
        platform: str,
        shipping_cost: Optional[float] = None
    ) -> Dict[str, float]:
        """
        Calculate profit for a sale

        Args:
            sold_price: Sale price
            cost: Cost of goods sold (COGS)
            platform: Platform name
            shipping_cost: Shipping cost (if applicable)

        Returns:
            Profit breakdown
        """
        fees = self.calculate_platform_fees(platform, sold_price)

        profit_data = {
            'sold_price': sold_price,
            'cost': cost or 0.0,
            'platform_fees': fees['total_fees'],
            'shipping_cost': shipping_cost or 0.0,
            'gross_profit': 0.0,
            'net_profit': 0.0,
            'profit_margin': 0.0
        }

        # Gross profit (before fees)
        profit_data['gross_profit'] = sold_price - profit_data['cost']

        # Net profit (after fees and shipping)
        profit_data['net_profit'] = (
            sold_price -
            profit_data['cost'] -
            fees['total_fees'] -
            profit_data['shipping_cost']
        )

        # Profit margin
        if sold_price > 0:
            profit_data['profit_margin'] = (profit_data['net_profit'] / sold_price) * 100

        return profit_data

    def generate_sales_report(
        self,
        user_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        platform: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate sales report for a date range

        Args:
            user_id: User ID
            start_date: Start date (default: 30 days ago)
            end_date: End date (default: now)
            platform: Filter by platform (optional)

        Returns:
            Sales report with totals and breakdown
        """
        # Default date range: last 30 days
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        # Query sold listings
        cursor = self.db._get_cursor()

        query = """
            SELECT * FROM listings
            WHERE user_id::text = %s::text
            AND status = 'sold'
            AND sold_date >= %s
            AND sold_date <= %s
        """
        params = [str(user_id), start_date, end_date]

        if platform:
            query += " AND sold_platform = %s"
            params.append(platform)

        query += " ORDER BY sold_date DESC"

        cursor.execute(query, params)
        sold_items = [dict(row) for row in cursor.fetchall()]

        # Calculate totals
        report = {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': (end_date - start_date).days
            },
            'summary': {
                'total_sales': len(sold_items),
                'total_revenue': 0.0,
                'total_cogs': 0.0,
                'total_fees': 0.0,
                'total_gross_profit': 0.0,
                'total_net_profit': 0.0,
                'average_sale_price': 0.0,
                'average_profit': 0.0,
                'average_margin': 0.0
            },
            'by_platform': {},
            'items': []
        }

        for item in sold_items:
            sold_price = float(item.get('sold_price') or item.get('price') or 0)
            cost = float(item.get('cost') or 0)
            platform_name = item.get('sold_platform', 'unknown')

            # Calculate profit for this item
            profit_data = self.calculate_profit(
                sold_price=sold_price,
                cost=cost,
                platform=platform_name
            )

            # Add to totals
            report['summary']['total_revenue'] += sold_price
            report['summary']['total_cogs'] += cost
            report['summary']['total_fees'] += profit_data['platform_fees']
            report['summary']['total_gross_profit'] += profit_data['gross_profit']
            report['summary']['total_net_profit'] += profit_data['net_profit']

            # Add to platform breakdown
            if platform_name not in report['by_platform']:
                report['by_platform'][platform_name] = {
                    'sales_count': 0,
                    'revenue': 0.0,
                    'fees': 0.0,
                    'profit': 0.0
                }

            report['by_platform'][platform_name]['sales_count'] += 1
            report['by_platform'][platform_name]['revenue'] += sold_price
            report['by_platform'][platform_name]['fees'] += profit_data['platform_fees']
            report['by_platform'][platform_name]['profit'] += profit_data['net_profit']

            # Add item details
            report['items'].append({
                'id': item['id'],
                'title': item['title'],
                'sold_date': item.get('sold_date'),
                'platform': platform_name,
                **profit_data
            })

        # Calculate averages
        if report['summary']['total_sales'] > 0:
            report['summary']['average_sale_price'] = (
                report['summary']['total_revenue'] / report['summary']['total_sales']
            )
            report['summary']['average_profit'] = (
                report['summary']['total_net_profit'] / report['summary']['total_sales']
            )

        if report['summary']['total_revenue'] > 0:
            report['summary']['average_margin'] = (
                report['summary']['total_net_profit'] / report['summary']['total_revenue']
            ) * 100

        return report

    def generate_1099k_report(
        self,
        user_id: int,
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate 1099-K reconciliation report

        Args:
            user_id: User ID
            year: Tax year (default: current year)

        Returns:
            1099-K report with platform breakdown
        """
        if not year:
            year = datetime.now().year

        start_date = datetime(year, 1, 1)
        end_date = datetime(year, 12, 31, 23, 59, 59)

        # Get annual sales report
        annual_report = self.generate_sales_report(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date
        )

        # 1099-K thresholds (2024+: $600 total, any number of transactions)
        threshold_amount = 600.00
        threshold_transactions = 0  # No minimum after 2024

        report = {
            'tax_year': year,
            'threshold': {
                'amount': threshold_amount,
                'transactions': threshold_transactions
            },
            'total_gross_revenue': annual_report['summary']['total_revenue'],
            'total_transactions': annual_report['summary']['total_sales'],
            'requires_1099k': annual_report['summary']['total_revenue'] >= threshold_amount,
            'platforms': {},
            'adjustments': {
                'refunds': 0.0,
                'chargebacks': 0.0,
                'adjusted_gross': annual_report['summary']['total_revenue']
            }
        }

        # Platform breakdown for 1099-K
        for platform_name, data in annual_report['by_platform'].items():
            report['platforms'][platform_name] = {
                'gross_revenue': data['revenue'],
                'transactions': data['sales_count'],
                'requires_1099k': data['revenue'] >= threshold_amount
            }

        return report

    def generate_profit_loss_statement(
        self,
        user_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generate Profit & Loss statement

        Args:
            user_id: User ID
            start_date: Start date
            end_date: End date

        Returns:
            P&L statement
        """
        sales_report = self.generate_sales_report(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date
        )

        pl_statement = {
            'period': sales_report['period'],
            'revenue': {
                'gross_sales': sales_report['summary']['total_revenue'],
                'refunds': 0.0,  # TODO: Track refunds
                'net_revenue': sales_report['summary']['total_revenue']
            },
            'cost_of_goods_sold': {
                'inventory_cost': sales_report['summary']['total_cogs'],
                'shipping': 0.0,  # TODO: Track shipping costs
                'total_cogs': sales_report['summary']['total_cogs']
            },
            'gross_profit': sales_report['summary']['total_gross_profit'],
            'operating_expenses': {
                'platform_fees': sales_report['summary']['total_fees'],
                'payment_processing': 0.0,  # Included in platform_fees
                'other_expenses': 0.0,
                'total_expenses': sales_report['summary']['total_fees']
            },
            'net_profit': sales_report['summary']['total_net_profit'],
            'margins': {
                'gross_margin': 0.0,
                'net_margin': sales_report['summary']['average_margin']
            }
        }

        # Calculate gross margin
        if pl_statement['revenue']['net_revenue'] > 0:
            pl_statement['margins']['gross_margin'] = (
                pl_statement['gross_profit'] / pl_statement['revenue']['net_revenue']
            ) * 100

        return pl_statement

    def export_to_csv(
        self,
        report: Dict[str, Any],
        report_type: str = 'sales'
    ) -> str:
        """
        Export report to CSV format

        Args:
            report: Report data
            report_type: Type of report ('sales', '1099k', 'pl')

        Returns:
            CSV string
        """
        import csv
        from io import StringIO

        output = StringIO()

        if report_type == 'sales':
            # Sales report CSV
            writer = csv.writer(output)
            writer.writerow([
                'Date', 'Title', 'Platform', 'Sale Price', 'Cost',
                'Fees', 'Gross Profit', 'Net Profit', 'Margin %'
            ])

            for item in report.get('items', []):
                writer.writerow([
                    item.get('sold_date', ''),
                    item.get('title', ''),
                    item.get('platform', ''),
                    f"${item.get('sold_price', 0):.2f}",
                    f"${item.get('cost', 0):.2f}",
                    f"${item.get('platform_fees', 0):.2f}",
                    f"${item.get('gross_profit', 0):.2f}",
                    f"${item.get('net_profit', 0):.2f}",
                    f"{item.get('profit_margin', 0):.2f}%"
                ])

            # Add summary row
            writer.writerow([])
            writer.writerow(['SUMMARY'])
            writer.writerow(['Total Sales', report['summary']['total_sales']])
            writer.writerow(['Total Revenue', f"${report['summary']['total_revenue']:.2f}"])
            writer.writerow(['Total Fees', f"${report['summary']['total_fees']:.2f}"])
            writer.writerow(['Total Profit', f"${report['summary']['total_net_profit']:.2f}"])

        return output.getvalue()


def generate_user_tax_report(
    user_id: int,
    db,
    year: Optional[int] = None
) -> Dict[str, Any]:
    """
    Convenience function to generate complete tax report for a user

    Args:
        user_id: User ID
        db: Database instance
        year: Tax year

    Returns:
        Complete tax report
    """
    generator = TaxReportGenerator(db)

    if not year:
        year = datetime.now().year

    # Generate all reports
    return {
        'year': year,
        'annual_sales': generator.generate_sales_report(
            user_id=user_id,
            start_date=datetime(year, 1, 1),
            end_date=datetime(year, 12, 31, 23, 59, 59)
        ),
        '1099k_report': generator.generate_1099k_report(user_id, year),
        'profit_loss': generator.generate_profit_loss_statement(
            user_id=user_id,
            start_date=datetime(year, 1, 1),
            end_date=datetime(year, 12, 31, 23, 59, 59)
        )
    }
