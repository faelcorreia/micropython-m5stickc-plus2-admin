import struct
import ubinascii  # type: ignore
import libs.colors as colors


class Bitmap:
    FILE_HEADER_SIZE = 14
    DIB_HEADER_SIZE = 40
    HEADERS_SIZE = FILE_HEADER_SIZE + DIB_HEADER_SIZE
    BASE64_HEADER = "data:image/bmp;base64,"

    @staticmethod
    def extract_pixels_from_base64bitmap(
        base64: str, expected_width=240, expected_height=135
    ) -> list[int]:
        """Extract pixels data from bitmap file"""
        if not base64.startswith(Bitmap.BASE64_HEADER):
            raise Exception(f"Wrong base64 format: expecting {Bitmap.BASE64_HEADER}")

        base64 = base64.replace(Bitmap.BASE64_HEADER, "")
        bitmap_bytes = ubinascii.a2b_base64(base64)

        if bitmap_bytes[0:2] != b"\x42\x4D":
            raise Exception("Wrong file format: expecting a bitmap file")
        if len(bitmap_bytes) < Bitmap.HEADERS_SIZE:
            raise Exception("Wrong file size: expecting a valid bitmap file")

        file_header = bitmap_bytes[0 : Bitmap.FILE_HEADER_SIZE]
        file_header_fields = struct.unpack("<2sIHHI", file_header)

        dib_header = bitmap_bytes[Bitmap.FILE_HEADER_SIZE : Bitmap.HEADERS_SIZE]
        header_fields = struct.unpack_from("<IiiHHiiiiii", dib_header)

        image_width = header_fields[1]
        image_height = header_fields[2]
        if image_width != expected_width or image_height != expected_height:
            raise Exception(
                f"Wrong image size: excepting {expected_width}x{expected_height} dimension"
            )

        bits_per_pixel = header_fields[4]
        if bits_per_pixel not in [16, 24]:
            raise Exception("Wrong bit count: expecting bitmap with 16 or 24 bits")

        row_padded = (image_width * bits_per_pixel + 31) // 32 * 4
        bitmap_pixels = []
        pixel_array_offset = file_header_fields[4]
        data_bytes = bitmap_bytes[
            pixel_array_offset : pixel_array_offset + (row_padded * image_height)
        ]
        end = len(data_bytes)
        for _ in range(image_height - 1, -1, -1):
            row = data_bytes[end - row_padded : end]
            for x in range(image_width):
                offset = x * (bits_per_pixel // 8)
                pixel = row[offset : offset + (bits_per_pixel // 8)]
                if bits_per_pixel == 16:
                    pixel = int.from_bytes(bytes(pixel), "little")
                    pixel = Bitmap.argb1555_to_rgb565(pixel)
                elif bits_per_pixel == 24:
                    pixel = colors.rgb565(r=pixel[2], g=pixel[1], b=pixel[0])
                bitmap_pixels.append(pixel)
            end -= row_padded
        return bitmap_pixels

    def argb1555_to_rgb565(argb1555):
        """Convert a 16-bit ARGB1555 value to a 16-bit RGB565 value."""
        alpha = (argb1555 >> 15) & 0x01
        red = (argb1555 >> 10) & 0x1F
        green = (argb1555 >> 5) & 0x1F
        blue = argb1555 & 0x1F

        green_565 = green << 1  # Expande de 5 bits para 6 bits

        rgb565 = (red << 11) | (green_565 << 5) | blue

        return rgb565
