"""
Image Processing Pipeline for AI Cross-Poster
Handles EXIF removal, auto-resize, compression, and optimization
"""

from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import io
import os


class ImagePipeline:
    """Process images for marketplace listings"""

    # Platform-specific image requirements
    PLATFORM_REQUIREMENTS = {
        'ebay': {
            'max_width': 1600,
            'max_height': 1600,
            'min_width': 500,
            'min_height': 500,
            'max_file_size': 12 * 1024 * 1024,  # 12MB
            'formats': ['JPEG', 'PNG', 'GIF'],
            'max_images': 24
        },
        'poshmark': {
            'max_width': 1280,
            'max_height': 1280,
            'min_width': 400,
            'min_height': 400,
            'max_file_size': 10 * 1024 * 1024,  # 10MB
            'formats': ['JPEG', 'PNG'],
            'max_images': 16
        },
        'mercari': {
            'max_width': 2048,
            'max_height': 2048,
            'min_width': 360,
            'min_height': 360,
            'max_file_size': 10 * 1024 * 1024,  # 10MB
            'formats': ['JPEG', 'PNG'],
            'max_images': 20
        },
        'etsy': {
            'max_width': 3000,
            'max_height': 3000,
            'min_width': 2000,
            'min_height': 2000,
            'max_file_size': 10 * 1024 * 1024,  # 10MB
            'formats': ['JPEG', 'PNG', 'GIF'],
            'max_images': 10
        },
        'generic': {
            'max_width': 1600,
            'max_height': 1600,
            'min_width': 500,
            'min_height': 500,
            'max_file_size': 10 * 1024 * 1024,  # 10MB
            'formats': ['JPEG', 'PNG'],
            'max_images': 12
        }
    }

    def __init__(self):
        """Initialize Image Pipeline"""
        # Check if PIL/Pillow is available
        try:
            from PIL import Image, ExifTags
            self.PIL_Image = Image
            self.PIL_ExifTags = ExifTags
            self.pil_available = True
        except ImportError:
            self.pil_available = False
            print("⚠️  Pillow not installed. Image processing features limited.")
            print("   Install with: pip install Pillow")

    def get_platform_requirements(self, platform: str) -> Dict[str, Any]:
        """
        Get image requirements for a platform

        Args:
            platform: Platform name

        Returns:
            Platform requirements dict
        """
        return self.PLATFORM_REQUIREMENTS.get(
            platform,
            self.PLATFORM_REQUIREMENTS['generic']
        )

    def remove_exif_data(self, image_path: str, output_path: Optional[str] = None) -> str:
        """
        Remove EXIF metadata from image for privacy

        Args:
            image_path: Path to image file
            output_path: Output path (overwrites input if None)

        Returns:
            Output file path
        """
        if not self.pil_available:
            raise ImportError("Pillow is required for EXIF removal")

        if not output_path:
            output_path = image_path

        # Open image
        img = self.PIL_Image.open(image_path)

        # Remove EXIF data by creating new image
        data = list(img.getdata())
        clean_image = self.PIL_Image.new(img.mode, img.size)
        clean_image.putdata(data)

        # Save without EXIF
        clean_image.save(output_path, quality=95, optimize=True)

        return output_path

    def resize_image(
        self,
        image_path: str,
        max_width: int,
        max_height: int,
        output_path: Optional[str] = None,
        maintain_aspect_ratio: bool = True
    ) -> str:
        """
        Resize image to fit within max dimensions

        Args:
            image_path: Path to image file
            max_width: Maximum width
            max_height: Maximum height
            output_path: Output path (overwrites input if None)
            maintain_aspect_ratio: Keep aspect ratio

        Returns:
            Output file path
        """
        if not self.pil_available:
            raise ImportError("Pillow is required for image resizing")

        if not output_path:
            output_path = image_path

        # Open image
        img = self.PIL_Image.open(image_path)

        # Get current dimensions
        width, height = img.size

        # Skip if already smaller
        if width <= max_width and height <= max_height:
            if output_path != image_path:
                img.save(output_path, quality=95, optimize=True)
            return output_path

        # Calculate new dimensions
        if maintain_aspect_ratio:
            # Calculate scaling factor
            width_ratio = max_width / width
            height_ratio = max_height / height
            scale = min(width_ratio, height_ratio)

            new_width = int(width * scale)
            new_height = int(height * scale)
        else:
            new_width = max_width
            new_height = max_height

        # Resize
        resized = img.resize((new_width, new_height), self.PIL_Image.Resampling.LANCZOS)

        # Save
        resized.save(output_path, quality=95, optimize=True)

        return output_path

    def auto_rotate(self, image_path: str, output_path: Optional[str] = None) -> str:
        """
        Auto-rotate image based on EXIF orientation

        Args:
            image_path: Path to image file
            output_path: Output path (overwrites input if None)

        Returns:
            Output file path
        """
        if not self.pil_available:
            raise ImportError("Pillow is required for auto-rotation")

        if not output_path:
            output_path = image_path

        # Open image
        img = self.PIL_Image.open(image_path)

        # Try to get EXIF orientation
        try:
            exif = img._getexif()
            if exif:
                orientation_key = None
                for key in self.PIL_ExifTags.TAGS.keys():
                    if self.PIL_ExifTags.TAGS[key] == 'Orientation':
                        orientation_key = key
                        break

                if orientation_key and orientation_key in exif:
                    orientation = exif[orientation_key]

                    # Rotate based on orientation
                    if orientation == 3:
                        img = img.rotate(180, expand=True)
                    elif orientation == 6:
                        img = img.rotate(270, expand=True)
                    elif orientation == 8:
                        img = img.rotate(90, expand=True)
        except (AttributeError, KeyError, IndexError):
            # No EXIF data or orientation tag
            pass

        # Save
        img.save(output_path, quality=95, optimize=True)

        return output_path

    def compress_image(
        self,
        image_path: str,
        output_path: Optional[str] = None,
        max_file_size: Optional[int] = None,
        quality: int = 85
    ) -> str:
        """
        Compress image to reduce file size

        Args:
            image_path: Path to image file
            output_path: Output path (overwrites input if None)
            max_file_size: Maximum file size in bytes (optional)
            quality: JPEG quality (1-100)

        Returns:
            Output file path
        """
        if not self.pil_available:
            raise ImportError("Pillow is required for image compression")

        if not output_path:
            output_path = image_path

        # Open image
        img = self.PIL_Image.open(image_path)

        # Convert RGBA to RGB if needed for JPEG
        if img.mode in ('RGBA', 'LA', 'P'):
            background = self.PIL_Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background

        # Save with compression
        if max_file_size:
            # Iteratively reduce quality to meet file size
            for q in range(quality, 10, -5):
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=q, optimize=True)

                if buffer.tell() <= max_file_size:
                    with open(output_path, 'wb') as f:
                        f.write(buffer.getvalue())
                    return output_path

            # If still too large, save at minimum quality
            img.save(output_path, format='JPEG', quality=10, optimize=True)
        else:
            img.save(output_path, format='JPEG', quality=quality, optimize=True)

        return output_path

    def process_image_for_platform(
        self,
        image_path: str,
        platform: str,
        output_path: Optional[str] = None,
        remove_exif: bool = True
    ) -> Dict[str, Any]:
        """
        Process image for a specific platform

        Args:
            image_path: Path to image file
            platform: Platform name
            output_path: Output path (temp file if None)
            remove_exif: Remove EXIF metadata

        Returns:
            Processing results
        """
        if not self.pil_available:
            return {
                'success': False,
                'error': 'Pillow library not available',
                'original_path': image_path
            }

        # Get platform requirements
        reqs = self.get_platform_requirements(platform)

        # Create temp output if not specified
        if not output_path:
            output_dir = Path(image_path).parent / 'processed'
            output_dir.mkdir(exist_ok=True)
            output_path = str(output_dir / Path(image_path).name)

        try:
            # Step 1: Auto-rotate
            self.auto_rotate(image_path, output_path)

            # Step 2: Remove EXIF
            if remove_exif:
                self.remove_exif_data(output_path, output_path)

            # Step 3: Resize if needed
            img = self.PIL_Image.open(output_path)
            width, height = img.size

            if width > reqs['max_width'] or height > reqs['max_height']:
                self.resize_image(
                    output_path,
                    reqs['max_width'],
                    reqs['max_height'],
                    output_path
                )

            # Step 4: Compress if needed
            file_size = os.path.getsize(output_path)
            if file_size > reqs['max_file_size']:
                self.compress_image(
                    output_path,
                    output_path,
                    max_file_size=reqs['max_file_size']
                )

            # Get final stats
            final_img = self.PIL_Image.open(output_path)
            final_width, final_height = final_img.size
            final_size = os.path.getsize(output_path)

            return {
                'success': True,
                'original_path': image_path,
                'output_path': output_path,
                'platform': platform,
                'original_size': {'width': width, 'height': height},
                'final_size': {'width': final_width, 'height': final_height},
                'original_file_size': os.path.getsize(image_path),
                'final_file_size': final_size,
                'meets_requirements': (
                    final_width >= reqs['min_width'] and
                    final_height >= reqs['min_height'] and
                    final_width <= reqs['max_width'] and
                    final_height <= reqs['max_height'] and
                    final_size <= reqs['max_file_size']
                )
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'original_path': image_path
            }

    def batch_process_images(
        self,
        image_paths: List[str],
        platform: str,
        output_dir: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Process multiple images for a platform

        Args:
            image_paths: List of image paths
            platform: Platform name
            output_dir: Output directory (creates 'processed' if None)

        Returns:
            List of processing results
        """
        results = []

        for image_path in image_paths:
            # Create output path
            if output_dir:
                output_path = str(Path(output_dir) / Path(image_path).name)
            else:
                output_path = None

            # Process image
            result = self.process_image_for_platform(
                image_path=image_path,
                platform=platform,
                output_path=output_path
            )

            results.append(result)

        return results


def process_listing_images(
    image_paths: List[str],
    platform: str = 'generic',
    output_dir: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Convenience function to process images for a listing

    Args:
        image_paths: List of image paths
        platform: Platform name
        output_dir: Output directory

    Returns:
        Processing results
    """
    pipeline = ImagePipeline()
    return pipeline.batch_process_images(
        image_paths=image_paths,
        platform=platform,
        output_dir=output_dir
    )
