# ITTAP - Image transfer tool for android phones

## Requirements
- Linux operating system (for now)
- libmtp and devices showing up under /run/user/{USER ID}/gvfs/ (most distros automatically do this)

## Functionality
Neatly organizes pictures into year/month subdirectories on desired location

To avoid issues during transfer the pictures are first dumped to a local temporary directory before being moved to the final location
