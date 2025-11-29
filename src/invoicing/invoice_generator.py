"""
Invoice Generation System for AI Cross-Poster
Generates PDF invoices, packing slips, and labels
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import json
import html


class InvoiceGenerator:
    """Generate invoices and related documents"""

    def __init__(self, business_info: Optional[Dict[str, str]] = None):
        """
        Initialize Invoice Generator

        Args:
            business_info: Business information (name, address, email, etc.)
        """
        self.business_info = business_info or {
            'business_name': 'Your Business Name',
            'address': '123 Main St',
            'city_state_zip': 'City, ST 12345',
            'email': 'contact@yourbusiness.com',
            'phone': '(555) 123-4567'
        }

    def generate_invoice_number(self, listing_id: int, date: Optional[datetime] = None) -> str:
        """
        Generate unique invoice number

        Args:
            listing_id: Listing ID
            date: Invoice date

        Returns:
            Invoice number (e.g., INV-2024-00123)
        """
        if not date:
            date = datetime.now()

        return f"INV-{date.year}-{listing_id:05d}"

    def calculate_totals(
        self,
        item_price: float,
        quantity: int = 1,
        tax_rate: float = 0.0,
        shipping: float = 0.0,
        discount: float = 0.0
    ) -> Dict[str, float]:
        """
        Calculate invoice totals

        Args:
            item_price: Item price
            quantity: Quantity
            tax_rate: Tax rate (e.g., 0.0825 for 8.25%)
            shipping: Shipping cost
            discount: Discount amount

        Returns:
            Totals breakdown
        """
        subtotal = item_price * quantity
        discount_amount = discount
        subtotal_after_discount = subtotal - discount_amount
        tax_amount = subtotal_after_discount * tax_rate
        total = subtotal_after_discount + tax_amount + shipping

        return {
            'subtotal': subtotal,
            'discount': discount_amount,
            'subtotal_after_discount': subtotal_after_discount,
            'tax_rate': tax_rate * 100,
            'tax_amount': tax_amount,
            'shipping': shipping,
            'total': total
        }

    def generate_invoice_html(
        self,
        invoice_data: Dict[str, Any]
    ) -> str:
        """
        Generate HTML invoice

        Args:
            invoice_data: Invoice data including item, buyer, totals

        Returns:
            HTML string
        """
        # Extract data
        invoice_number = invoice_data.get('invoice_number', 'N/A')
        invoice_date = invoice_data.get('date', datetime.now().strftime('%Y-%m-%d'))
        buyer = invoice_data.get('buyer', {})
        item = invoice_data.get('item', {})
        totals = invoice_data.get('totals', {})
        notes = invoice_data.get('notes', '')

        html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Invoice {html.escape(invoice_number)}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 30px;
            border-bottom: 2px solid #0066cc;
            padding-bottom: 20px;
        }}
        .business-info {{
            flex: 1;
        }}
        .invoice-info {{
            flex: 1;
            text-align: right;
        }}
        .business-name {{
            font-size: 24px;
            font-weight: bold;
            color: #0066cc;
            margin-bottom: 10px;
        }}
        .invoice-title {{
            font-size: 32px;
            font-weight: bold;
            color: #0066cc;
        }}
        .section {{
            margin: 20px 0;
        }}
        .section-title {{
            font-weight: bold;
            font-size: 14px;
            color: #0066cc;
            margin-bottom: 10px;
            text-transform: uppercase;
        }}
        .buyer-info {{
            background: #f5f5f5;
            padding: 15px;
            border-radius: 5px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th {{
            background: #0066cc;
            color: white;
            padding: 12px;
            text-align: left;
        }}
        td {{
            padding: 12px;
            border-bottom: 1px solid #ddd;
        }}
        .totals-table {{
            width: 300px;
            margin-left: auto;
        }}
        .totals-table td {{
            text-align: right;
        }}
        .total-row {{
            font-weight: bold;
            font-size: 18px;
            background: #f0f0f0;
        }}
        .notes {{
            background: #fffbf0;
            padding: 15px;
            border-left: 4px solid #ffa500;
            margin: 20px 0;
        }}
        .footer {{
            text-align: center;
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #666;
            font-size: 12px;
        }}
        @media print {{
            body {{
                padding: 0;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="business-info">
            <div class="business-name">{html.escape(self.business_info.get('business_name', ''))}</div>
            <div>{html.escape(self.business_info.get('address', ''))}</div>
            <div>{html.escape(self.business_info.get('city_state_zip', ''))}</div>
            <div>Email: {html.escape(self.business_info.get('email', ''))}</div>
            <div>Phone: {html.escape(self.business_info.get('phone', ''))}</div>
        </div>
        <div class="invoice-info">
            <div class="invoice-title">INVOICE</div>
            <div style="margin-top: 10px;">
                <div><strong>Invoice #:</strong> {html.escape(invoice_number)}</div>
                <div><strong>Date:</strong> {html.escape(invoice_date)}</div>
            </div>
        </div>
    </div>

    <div class="section">
        <div class="section-title">Bill To</div>
        <div class="buyer-info">
            <div><strong>{html.escape(buyer.get('name', 'N/A'))}</strong></div>
            <div>{html.escape(buyer.get('email', ''))}</div>
            <div>{html.escape(buyer.get('address', ''))}</div>
            <div>{html.escape(buyer.get('city_state_zip', ''))}</div>
        </div>
    </div>

    <div class="section">
        <div class="section-title">Items</div>
        <table>
            <thead>
                <tr>
                    <th>Description</th>
                    <th>SKU</th>
                    <th style="text-align: right;">Qty</th>
                    <th style="text-align: right;">Unit Price</th>
                    <th style="text-align: right;">Total</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>{html.escape(item.get('title', 'N/A'))}</td>
                    <td>{html.escape(item.get('sku', 'N/A'))}</td>
                    <td style="text-align: right;">{item.get('quantity', 1)}</td>
                    <td style="text-align: right;">${item.get('price', 0.0):.2f}</td>
                    <td style="text-align: right;">${totals.get('subtotal', 0.0):.2f}</td>
                </tr>
            </tbody>
        </table>
    </div>

    <table class="totals-table">
        <tr>
            <td>Subtotal:</td>
            <td>${totals.get('subtotal', 0.0):.2f}</td>
        </tr>
"""

        # Add discount if present
        if totals.get('discount', 0) > 0:
            html_template += f"""
        <tr>
            <td>Discount:</td>
            <td>-${totals.get('discount', 0.0):.2f}</td>
        </tr>
"""

        # Add tax if present
        if totals.get('tax_amount', 0) > 0:
            html_template += f"""
        <tr>
            <td>Tax ({totals.get('tax_rate', 0):.2f}%):</td>
            <td>${totals.get('tax_amount', 0.0):.2f}</td>
        </tr>
"""

        # Add shipping if present
        if totals.get('shipping', 0) > 0:
            html_template += f"""
        <tr>
            <td>Shipping:</td>
            <td>${totals.get('shipping', 0.0):.2f}</td>
        </tr>
"""

        html_template += f"""
        <tr class="total-row">
            <td>TOTAL:</td>
            <td>${totals.get('total', 0.0):.2f}</td>
        </tr>
    </table>

"""

        # Add notes if present
        if notes:
            html_template += f"""
    <div class="notes">
        <strong>Notes:</strong><br>
        {html.escape(notes)}
    </div>
"""

        html_template += """
    <div class="footer">
        <p>Thank you for your business!</p>
        <p>Please remit payment within 30 days.</p>
    </div>
</body>
</html>
"""

        return html_template

    def generate_packing_slip_html(
        self,
        order_data: Dict[str, Any]
    ) -> str:
        """
        Generate HTML packing slip

        Args:
            order_data: Order data

        Returns:
            HTML string
        """
        order_number = order_data.get('order_number', 'N/A')
        order_date = order_data.get('date', datetime.now().strftime('%Y-%m-%d'))
        buyer = order_data.get('buyer', {})
        items = order_data.get('items', [])
        storage_location = order_data.get('storage_location', 'N/A')

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Packing Slip {html.escape(order_number)}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            text-align: center;
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 20px;
            border-bottom: 2px solid #333;
            padding-bottom: 10px;
        }}
        .section {{
            margin: 15px 0;
        }}
        .label {{
            font-weight: bold;
            color: #666;
        }}
        .ship-to {{
            background: #f0f0f0;
            padding: 15px;
            border: 2px solid #333;
            margin: 20px 0;
        }}
        .ship-to-label {{
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 10px;
            text-align: left;
            border: 1px solid #ddd;
        }}
        th {{
            background: #f0f0f0;
        }}
        .storage {{
            background: #fffacd;
            padding: 10px;
            border: 2px dashed #ffa500;
            margin: 20px 0;
            text-align: center;
            font-weight: bold;
            font-size: 18px;
        }}
    </style>
</head>
<body>
    <div class="header">PACKING SLIP</div>

    <div class="section">
        <span class="label">Order #:</span> {html.escape(order_number)}<br>
        <span class="label">Date:</span> {html.escape(order_date)}
    </div>

    <div class="ship-to">
        <div class="ship-to-label">SHIP TO:</div>
        <div><strong>{html.escape(buyer.get('name', ''))}</strong></div>
        <div>{html.escape(buyer.get('address', ''))}</div>
        <div>{html.escape(buyer.get('city_state_zip', ''))}</div>
    </div>

    <div class="storage">
        📦 Storage Location: {html.escape(storage_location)}
    </div>

    <table>
        <thead>
            <tr>
                <th>Item</th>
                <th>SKU</th>
                <th>Qty</th>
            </tr>
        </thead>
        <tbody>
"""

        # Add items
        if isinstance(items, list):
            for item in items:
                html += f"""
            <tr>
                <td>{html.escape(item.get('title', 'N/A'))}</td>
                <td>{html.escape(item.get('sku', 'N/A'))}</td>
                <td>{item.get('quantity', 1)}</td>
            </tr>
"""

        html += """
        </tbody>
    </table>

    <div style="margin-top: 40px; text-align: center; color: #666;">
        <p>Thank you for your purchase!</p>
    </div>
</body>
</html>
"""

        return html

    def create_invoice(
        self,
        listing: Dict[str, Any],
        buyer: Dict[str, str],
        tax_rate: float = 0.0,
        shipping: float = 0.0,
        discount: float = 0.0,
        notes: str = "",
        save_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create invoice for a listing

        Args:
            listing: Listing data
            buyer: Buyer information
            tax_rate: Tax rate (decimal, e.g., 0.0825)
            shipping: Shipping cost
            discount: Discount amount
            notes: Invoice notes
            save_path: Path to save HTML file (optional)

        Returns:
            Invoice data and HTML
        """
        # Generate invoice number
        invoice_number = self.generate_invoice_number(
            listing.get('id', 0),
            datetime.now()
        )

        # Calculate totals
        totals = self.calculate_totals(
            item_price=listing.get('price', 0.0),
            quantity=listing.get('quantity', 1),
            tax_rate=tax_rate,
            shipping=shipping,
            discount=discount
        )

        # Build invoice data
        invoice_data = {
            'invoice_number': invoice_number,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'buyer': buyer,
            'item': listing,
            'totals': totals,
            'notes': notes,
            'status': 'unpaid'
        }

        # Generate HTML
        html = self.generate_invoice_html(invoice_data)

        # Save if path provided
        if save_path:
            Path(save_path).write_text(html, encoding='utf-8')
            invoice_data['file_path'] = save_path

        invoice_data['html'] = html

        return invoice_data

    def create_packing_slip(
        self,
        listing: Dict[str, Any],
        buyer: Dict[str, str],
        save_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create packing slip for an order

        Args:
            listing: Listing data
            buyer: Buyer information
            save_path: Path to save HTML file (optional)

        Returns:
            Packing slip data and HTML
        """
        order_data = {
            'order_number': f"ORD-{listing.get('id', 0):05d}",
            'date': datetime.now().strftime('%Y-%m-%d'),
            'buyer': buyer,
            'items': [listing],
            'storage_location': listing.get('storage_location', 'N/A')
        }

        # Generate HTML
        html = self.generate_packing_slip_html(order_data)

        # Save if path provided
        if save_path:
            Path(save_path).write_text(html, encoding='utf-8')
            order_data['file_path'] = save_path

        order_data['html'] = html

        return order_data


def generate_invoice_for_sale(
    listing: Dict[str, Any],
    buyer_info: Dict[str, str],
    business_info: Optional[Dict[str, str]] = None,
    tax_rate: float = 0.0,
    shipping: float = 0.0
) -> Dict[str, Any]:
    """
    Convenience function to generate invoice for a sale

    Args:
        listing: Listing data
        buyer_info: Buyer information
        business_info: Business information
        tax_rate: Tax rate
        shipping: Shipping cost

    Returns:
        Invoice data with HTML
    """
    generator = InvoiceGenerator(business_info=business_info)
    return generator.create_invoice(
        listing=listing,
        buyer=buyer_info,
        tax_rate=tax_rate,
        shipping=shipping
    )
