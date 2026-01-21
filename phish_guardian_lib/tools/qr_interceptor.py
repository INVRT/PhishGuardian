import cv2
from pyzbar.pyzbar import decode

def extract_qr_urls(image_path: str):
    """
    Extracts QR code payload(s) from an image and returns a list of URLs.
    """
    try:
        img = cv2.imread(image_path)
        decoded = decode(img)

        urls = []
        for obj in decoded:
            payload = obj.data.decode('utf-8')
            if payload.startswith("http://") or payload.startswith("https://"):
                urls.append(payload)

        return urls

    except Exception as e:
        print(f"QR decoding failed: {e}")
        return []
