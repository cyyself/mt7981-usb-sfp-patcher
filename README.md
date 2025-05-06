# tr3000-ubootmod-512m-flash-patcher

Patch existing OpenWRT firmware to use the 512M flash of cudy TR3000.

## Tested Device

- Cudy TR3000 (with prebuilt 512M U-Boot with ubi reg = <0x5c0000 0x1fa40000>)

## Tested OpenWRT Versions

- ImmortalWrt 24.10.1 (ubootmod)

## How to use

### Presquites

- Install U-Boot Tools and Device Tree Compiler

Debian / Ubuntu: `sudo apt install u-boot-tools device-tree-compiler`

Arch Linux: `sudo pacman -S uboot-tools dtc`

Homebrew: `brew install u-boot-tools dtc`

- Install python3 with hashlib, zlib

### Steps

1. Clone this repository

```bash
git clone https://github.com/cyyself/mt7981-usb-sfp-patcher.git -b tr3000-ubootmod-512m-flash
cd mt7981-usb-sfp-patcher
```

#### For OpenWRT ITB firmware

1. Patch the firmware

```bash
wget https://downloads.immortalwrt.org/releases/24.10.1/targets/mediatek/filogic/immortalwrt-24.10.1-mediatek-filogic-cudy_tr3000-v1-ubootmod-squashfs-sysupgrade.itb
python3 patch_itb.py immortalwrt-24.10.1-mediatek-filogic-cudy_tr3000-v1-ubootmod-squashfs-sysupgrade.itb patched.itb
```

2. (Optional) Verify the patched dts

```bash
diff build/orig.dts build/patched.dts
```

```diff
362c362
<                                               reg = <0x5c0000 0x7a40000>;
---
>                                               reg = <0x5c0000 0x1fa40000>;
```

3. Use `sysupgrade -F` or LuCI to flash the patched firmware

It's normal to get a warning "Image check failed", but "Force upgrade" should work.
