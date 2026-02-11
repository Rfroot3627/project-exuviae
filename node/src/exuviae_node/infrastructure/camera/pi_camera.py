import shutil
import subprocess
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

class LibcameraAdapter:
    """
    Infrastructure adapter for Raspberry Pi Camera (libcamera).
    Strict SSOT: Only supports what the contract allows (jpeg).
    """
    def __init__(self):
        # Detect available command: rpicam-still (Bookworm+) or libcamera-still (Bullseye)
        if shutil.which("rpicam-still"):
            self.cmd = "rpicam-still"
        elif shutil.which("libcamera-still"):
            self.cmd = "libcamera-still"
        else:
            self.cmd = None
            logger.warning("No libcamera command found. Adapter will operate in MOCK mode.")

    def capture(self, output_path: Path, width: int, height: int, timeout_ms: int = 5000) -> bool:
        """
        Capture a JPEG image.
        """
        if self.cmd:
            # Real Capture
            # -o: output
            # -t: timeout (time before capture, practically 1ms for immediate if AF not needed, 
            #     but let's verify usage. Standard is -t <delay_ms>). 
            #     Let's use slight delay to allow AWB/AE if needed, or minimal.
            # --width, --height: resolution
            # -n: no preview
            cmd_args = [
                self.cmd,
                "-o", str(output_path),
                "--width", str(width),
                "--height", str(height),
                "-t", "200",  # 200ms for basic AWB/AE settle
                "-n"
            ]
            
            try:
                logger.info(f"Executing capture: {' '.join(cmd_args)}")
                # Run with timeout to prevent hang
                subprocess.run(cmd_args, check=True, timeout=timeout_ms/1000 + 2)
                return output_path.exists()
            except subprocess.CalledProcessError as e:
                logger.error(f"Camera capture failed (rc={e.returncode}): {e}")
                return False
            except subprocess.TimeoutExpired:
                logger.error("Camera capture timed out")
                return False
            except Exception as e:
                logger.error(f"Unexpected camera error: {e}")
                return False
        else:
            # Mock Capture (Windows/Non-Pi)
            logger.info(f"[MOCK] Simulating capture to {output_path} ({width}x{height})")
            try:
                # Create a black dummy JPEG
                # Minimal valid JPEG header + End of Image
                with open(output_path, "wb") as f:
                    f.write(b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xda\x00\x08\x01\x01\x00\x00\x00@\x00\xff\xd9')
                return True
            except Exception as e:
                logger.error(f"Mock capture failed: {e}")
                return False
