# Lenovo Boot Screen Changer

This is free software for Linux that can customize the boot logo on many
Lenovo laptops, including some Thinkpad models.

Only a recent copy of Python 3 is required to run the program; no
external libraries or build tools are needed.

Please note the license terms of the software, including that it is
provided without any warranty. To operate, this software must change
EFI variables read by your system firmware, and this has the potential
to be a dangerous operation. Care has been taken to make sure the
program exits if an error is detected, but the safety of the operation
cannot be guaranteed on untested systems.

## Usage

Run `python change.py` to read the existing data from the EFI variables.
Among the data printed will be the maximum accepted resolution for a
boot logo image, as well as accepted file formats. You will need to
provide your own logo image to use. Note that the image can be smaller
than the maximum size, and it will be placed approximately in the center
of the screen.

Run `sudo python change.py -f path/to/logo.bmp` to provide your own
logo. Note that this program does not check to make sure that your
provided file is in the right format, or that it is an acceptable size.

## FAQ

1. The program claims to have enabled the custom boot logo, but nothing
has changed. Why?

If you have a supported system, this can happen if you have multiple
drives. You may have a pre-existing custom logo placed on the drive that
the firmware searches first. Try mounting the EFI System Partition on
this drive and removing the logo image.

## Disclaimer

This software is not created or endorsed by Lenovo Group Limited.
