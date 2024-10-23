#!/usr/bin/env python3
# Copyright (C) 2024 A. Fontenot (https://github.com/afontenot)
# SPDX-License-identifier: MIT
import argparse
import fcntl
import struct
from binascii import crc32
from os import getuid
from pathlib import Path
from shutil import copyfile


EFI_PATH = Path("/efi")
EFIVAR_PATH = Path("/sys/firmware/efi/efivars")
DESP_FMT = "=i?iiB"
DESP_VAR = "LBLDESP-871455d0-5576-4fb8-9865-af0824463b9e"
DVC_VAR = "LBLDVC-871455d1-5576-4fb8-9865-af0824463c9f"


def set_file_immutability(path: Path | str, immutable: bool):
    FS_IOC_GETFLAGS = 0x80086601
    FS_IOC_SETFLAGS = 0x40086602
    FS_IMMUTABLE_FL = 0x00000010
    with open(path) as f:
        flags = bytearray(4)
        # send ioctl requesting existing flags on file -> flags
        fcntl.ioctl(f.fileno(), FS_IOC_GETFLAGS, flags, True)
        flags = struct.unpack("=L", flags)[0]
        # set immutable bit as requested
        if immutable:
            flags |= FS_IMMUTABLE_FL
        else:
            flags &= ~FS_IMMUTABLE_FL
        fcntl.ioctl(f.fileno(), FS_IOC_SETFLAGS, struct.pack("=L", flags))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d", "--disable", action="store_true", help="disable the custom boot logo"
    )
    parser.add_argument(
        "-e",
        "--efi",
        help="the path to your mounted EFI system partition",
        default=EFI_PATH,
        type=Path,
    )
    parser.add_argument("-f", "--file", help="image file to use as a logo")
    parser.add_argument(
        "--vars",
        help="the path to your EFI vars",
        default=EFIVAR_PATH,
        type=Path,
    )
    args = parser.parse_args()

    desp_path = args.vars / DESP_VAR
    dvc_path = args.vars / DVC_VAR

    try:
        with open(desp_path, "rb") as f:
            desp = f.read()
        with open(dvc_path, "rb") as f:
            dvc = f.read()
    except FileNotFoundError:
        print(
            "Could not open Lenovo EFI variables. "
            "Your system probably does not support changing the boot logo."
        )
        return

    try:
        desp = list(struct.unpack(DESP_FMT, desp))
        assert len(dvc) == 44
    except (AssertionError, struct.error):
        print(
            "Could not parse Lenovo EFI variables. "
            "Your system probably might not support changing the boot logo."
        )
        return

    jpeg_support = bool(desp[4] & 0x01)
    bmp_support = bool(desp[4] & 0x10)
    png_support = bool(desp[4] & 0x20)
    support = [
        x[0]
        for x in (
            ("JPG", jpeg_support),
            ("BMP", bmp_support),
            ("PNG", png_support),
        )
        if x[1]
    ]

    print(
        "Status:\n"
        f"Logo enabled: {desp[1]}\n"
        f"Logo maximum resolution: {desp[2]}x{desp[3]}\n"
        f"Logo format support: {", ".join(support)}\n"
        f"Logo CRC32: {dvc[8:12].hex()}"
    )

    if not args.file and not args.disable:
        return

    if not getuid() == 0:
        print("You need to be root to perform this operation.")
        return

    if args.disable:
        # Disable logo in DESP
        desp[1] = False
        desp = struct.pack(DESP_FMT, *desp)
        set_file_immutability(desp_path, False)
        with open(desp_path, "wb") as f:
            f.write(desp)
        print("Boot logo has been disabled.")
        return

    # Validate sanity of file type
    ext = args.file.split(".")[-1].upper()
    if ext not in support:
        print(
            f"extension of {args.file} is {ext}; "
            "this indicates an unsupported file type"
        )
        return

    # Copy the logo file to the ESP System Partition
    outpath = args.efi / f"EFI/Lenovo/Logo/mylogo_{desp[2]}x{desp[3]}.{ext.lower()}"

    print(f"Logo file will be copied to {outpath}")
    if input("Confirm (Y/n): ") == "n":
        return

    outpath.parent.mkdir(exist_ok=True, parents=True)
    copyfile(args.file, outpath)

    # Calculate crc32 for logo and set it in the DVC
    with open(args.file, "rb") as f:
        csum = struct.pack("=I", crc32(f.read(512)))

    assert len(csum) == 4
    dvc = dvc[0:8] + csum + dvc[12:]

    set_file_immutability(dvc_path, False)
    with open(dvc_path, "wb") as f:
        f.write(dvc)
    set_file_immutability(dvc_path, True)

    # Enable logo in DESP
    desp[1] = True
    desp = struct.pack(DESP_FMT, *desp)
    set_file_immutability(desp_path, False)
    with open(desp_path, "wb") as f:
        f.write
    set_file_immutability(desp_path, True)

    print("Boot logo has been enabled.")


if __name__ == "__main__":
    main()
