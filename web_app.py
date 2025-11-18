#!/usr/bin/env python3
"""
AI Cross-Poster Web App
========================
Mobile-friendly web interface for inventory management and cross-platform listing.

Run with:
    python web_app.py

Or deploy to:
    - Heroku
    - DigitalOcean
    - AWS
    - Your own server
"""

import os
import uuid
import json
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

from src.schema import UnifiedListing, Photo, Price, ListingCondition, Shipping, ItemSpecifics
from src.database import get_db
import csv
from io import StringIO, BytesIO

# Load environment
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
app.config['UPLOAD_FOLDER'] = './data/uploads'

# Ensure upload folder exists
Path(app.config['UPLOAD_FOLDER']).mkdir(parents=True, exist_ok=True)

# Initialize services
db = get_db()


# ============================================================================
# ROUTES
# ============================================================================

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')


@app.route('/create')
def create_listing():
    """Create new listing page"""
    return render_template('create.html')


@app.route('/drafts')
def drafts():
    """View saved drafts"""
    drafts_list = db.get_drafts(limit=100)
    return render_template('drafts.html', drafts=drafts_list)


@app.route('/listings')
def listings():
    """View active listings"""
    cursor = db.conn.cursor()
    cursor.execute("""
        SELECT l.*, GROUP_CONCAT(pl.platform || ':' || pl.status) as platform_statuses
        FROM listings l
        LEFT JOIN platform_listings pl ON l.id = pl.listing_id
        WHERE l.status != 'draft'
        GROUP BY l.id
        ORDER BY l.created_at DESC
        LIMIT 50
    """)
    listings_list = [dict(row) for row in cursor.fetchall()]
    return render_template('listings.html', listings=listings_list)


@app.route('/notifications')
def notifications():
    """View notifications"""
    if notification_manager:
        notifs = notification_manager.get_recent_notifications(limit=50)
    else:
        notifs = []
    return render_template('notifications.html', notifications=notifs)


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/api/upload-photos', methods=['POST'])
def upload_photos():
    """Handle photo uploads"""
    if 'photos' not in request.files:
        return jsonify({'error': 'No photos provided'}), 400

    files = request.files.getlist('photos')
    if not files or files[0].filename == '':
        return jsonify({'error': 'No photos selected'}), 400

    # Save photos
    photo_paths = []
    for file in files:
        if file:
            filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            photo_paths.append(filepath)

    # Store in session
    session['photo_paths'] = photo_paths

    return jsonify({
        'success': True,
        'count': len(photo_paths),
        'paths': photo_paths
    })


@app.route('/api/analyze', methods=['POST'])
def analyze_photos():
    """Analyze photos with AI"""
    photo_paths = session.get('photo_paths', [])

    if not photo_paths:
        return jsonify({'error': 'No photos to analyze'}), 400

    try:
        from src.ai.gemini_classifier import GeminiClassifier

        # Create photo objects
        photo_objects = [
            Photo(url="", local_path=p, order=i, is_primary=(i == 0))
            for i, p in enumerate(photo_paths)
        ]

        # Analyze with Gemini
        classifier = GeminiClassifier.from_env()
        analysis = classifier.analyze_item(photo_objects)

        if "error" in analysis:
            return jsonify({'error': analysis['error']}), 500

        return jsonify({
            'success': True,
            'analysis': analysis
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/save-draft', methods=['POST'])
def save_draft():
    """Save listing as draft"""
    data = request.json
    photo_paths = session.get('photo_paths', [])

    if not photo_paths:
        return jsonify({'error': 'No photos uploaded'}), 400

    try:
        listing_uuid = str(uuid.uuid4())

        # Copy photos to permanent storage
        draft_photos_dir = Path("data/draft_photos") / listing_uuid
        draft_photos_dir.mkdir(parents=True, exist_ok=True)

        permanent_photo_paths = []
        for i, photo_path in enumerate(photo_paths):
            ext = Path(photo_path).suffix
            new_filename = f"photo_{i:02d}{ext}"
            permanent_path = draft_photos_dir / new_filename

            # Copy file
            import shutil
            shutil.copy2(photo_path, permanent_path)
            permanent_photo_paths.append(str(permanent_path))

        # Save to database
        listing_id = db.create_listing(
            listing_uuid=listing_uuid,
            title=data.get('title', 'Untitled'),
            description=data.get('description', ''),
            price=float(data.get('price', 0)),
            condition=data.get('condition', 'good'),
            photos=permanent_photo_paths,
            cost=float(data.get('cost')) if data.get('cost') else None,
            quantity=int(data.get('quantity', 1)),
            storage_location=data.get('storage_location'),
            attributes={
                'brand': data.get('brand'),
                'size': data.get('size'),
                'color': data.get('color'),
                'shipping_cost': float(data.get('shipping_cost', 0)),
            }
        )

        # Clear session
        session.pop('photo_paths', None)

        return jsonify({
            'success': True,
            'listing_id': listing_id
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/export-csv', methods=['GET'])
def export_csv():
    """Export all drafts to CSV"""
    try:
        drafts = db.get_drafts(limit=1000)

        # Create CSV in memory
        output = StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(['ID', 'Title', 'Description', 'Price', 'Cost', 'Condition',
                        'Brand', 'Size', 'Color', 'Storage Location', 'Quantity',
                        'Shipping Cost', 'Created'])

        # Data
        for draft in drafts:
            # Parse attributes
            attrs = {}
            if draft.get('attributes'):
                try:
                    attrs = json.loads(draft['attributes'])
                except:
                    pass

            writer.writerow([
                draft['id'],
                draft['title'],
                draft['description'],
                draft['price'],
                draft.get('cost', ''),
                draft['condition'],
                attrs.get('brand', ''),
                attrs.get('size', ''),
                attrs.get('color', ''),
                draft.get('storage_location', ''),
                draft.get('quantity', 1),
                attrs.get('shipping_cost', ''),
                draft['created_at']
            ])

        # Send file
        from flask import Response
        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=listings.csv'}
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/import-csv', methods=['POST'])
def import_csv():
    """Import CSV to update storage locations"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    try:
        # Read CSV
        stream = StringIO(file.stream.read().decode('utf-8'))
        reader = csv.DictReader(stream)

        updated = 0
        for row in reader:
            listing_id = row.get('ID')
            storage_location = row.get('Storage Location')

            if listing_id and storage_location:
                # Update storage location
                cursor = db.conn.cursor()
                cursor.execute("""
                    UPDATE listings
                    SET storage_location = ?
                    WHERE id = ?
                """, (storage_location, listing_id))
                db.conn.commit()
                updated += 1

        return jsonify({
            'success': True,
            'updated': updated
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/mark-sold', methods=['POST'])
def mark_sold():
    """Mark listing as sold"""
    data = request.json

    try:
        listing_id = int(data['listing_id'])
        sold_price = float(data.get('sold_price')) if data.get('sold_price') else None
        quantity_sold = int(data.get('quantity_sold', 1))

        # Get listing
        listing = db.get_listing(listing_id)
        if not listing:
            return jsonify({'error': 'Listing not found'}), 404

        # Update quantity
        current_quantity = listing.get('quantity', 1)
        remaining_quantity = max(0, current_quantity - quantity_sold)

        cursor = db.conn.cursor()
        if remaining_quantity == 0:
            # Mark as sold
            cursor.execute("""
                UPDATE listings
                SET status = 'sold',
                    quantity = 0,
                    sold_price = ?,
                    sold_date = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (sold_price, listing_id))
        else:
            # Just reduce quantity
            cursor.execute("""
                UPDATE listings
                SET quantity = ?
                WHERE id = ?
            """, (remaining_quantity, listing_id))

        db.conn.commit()

        return jsonify({
            'success': True,
            'storage_location': listing.get('storage_location'),
            'remaining_quantity': remaining_quantity
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/delete-draft/<int:listing_id>', methods=['DELETE'])
def delete_draft(listing_id):
    """Delete a draft"""
    try:
        listing = db.get_listing(listing_id)

        if listing:
            # Delete photos directory
            import shutil
            if listing.get('listing_uuid'):
                draft_photos_dir = Path("data/draft_photos") / listing['listing_uuid']
                if draft_photos_dir.exists():
                    shutil.rmtree(draft_photos_dir)

        db.delete_listing(listing_id)

        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == '__main__':
    # Development server
    app.run(
        host='0.0.0.0',  # Accessible from other devices on network
        port=5000,
        debug=True
    )
