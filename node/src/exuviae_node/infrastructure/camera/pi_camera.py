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
        # Detect available command: rpicam-still (Bookworm+), libcamera-still (Bullseye), or ffmpeg (USB Camera)
        self.cmd_type = "mock"
        self.cmd = None
        
        if shutil.which("rpicam-still"):
            self.cmd = "rpicam-still"
            self.cmd_type = "libcamera"
        elif shutil.which("libcamera-still"):
            self.cmd = "libcamera-still"
            self.cmd_type = "libcamera"
        elif shutil.which("ffmpeg"):
            self.cmd = "ffmpeg"
            self.cmd_type = "ffmpeg"
        else:
            logger.warning("No camera command found (rpicam/libcamera/ffmpeg). Adapter will operate in MOCK mode.")

    def capture(self, output_path: Path, width: int, height: int, timeout_ms: int = 5000) -> bool:
        """
        Capture a JPEG image.
        """
        if self.cmd_type == "libcamera":
            # Real Capture via libcamera
            cmd_args = [
                self.cmd,
                "-o", str(output_path),
                "--width", str(width),
                "--height", str(height),
                "-t", "200",  # 200ms for basic AWB/AE settle
                "-n"
            ]
            
            try:
                logger.info(f"Executing libcamera capture: {' '.join(cmd_args)}")
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
                
        elif self.cmd_type == "ffmpeg":
            # Generic Linux USB Webcam using v4l2 and ffmpeg
            cmd_args = [
                "sudo", self.cmd,
                "-y", # overwrite output
                "-f", "v4l2",
                "-video_size", f"{width}x{height}",
                "-i", "/dev/video0",
                "-frames:v", "1",
                "-update", "1",
                "-loglevel", "error",
                str(output_path)
            ]
            
            try:
                logger.info(f"Executing ffmpeg capture: {' '.join(cmd_args)}")
                result = subprocess.run(cmd_args, timeout=timeout_ms/1000 + 2,
                                        capture_output=True)
                if output_path.exists():
                    if result.returncode != 0:
                        logger.warning(
                            f"FFmpeg exited with non-zero rc={result.returncode} "
                            f"but file exists — treating as success. "
                            f"stderr: {result.stderr.decode(errors='replace')[-200:]}"
                        )
                    return True
                else:
                    logger.error(
                        f"FFmpeg rc={result.returncode}, file not created. "
                        f"stderr: {result.stderr.decode(errors='replace')[-400:]}"
                    )
                    return False
            except subprocess.TimeoutExpired:
                logger.error("FFmpeg capture timed out")
                return False
            except Exception as e:
                logger.error(f"Unexpected ffmpeg error: {e}")
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
