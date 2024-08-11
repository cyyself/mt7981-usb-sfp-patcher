# mt7981-usb-sfp-patcher

Patch existing OpenWRT firmware (sysupgrade.itb) to use the USB3 on the MT7981 to connect to 2500Base-X SFP module.

## Tested Device

- CMCC RAX3000M

## Tested OpenWRT Versions

- 23.05.4

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
git clone https://github.com/cyyself/mt7981-usb-sfp-patcher.git
```

2. Patch the firmware

```bash
wget https://downloads.openwrt.org/releases/23.05.4/targets/mediatek/filogic/openwrt-23.05.4-mediatek-filogic-cmcc_rax3000m-squashfs-sysupgrade.itb
python3 patch_itb.py openwrt-23.05.4-mediatek-filogic-cmcc_rax3000m-squashfs-sysupgrade.itb patched.itb
```

1. (Optional) Verify the patched dts

```bash
diff build/orig.dts build/patched.dts
```

```diff
8c8
<       model = "CMCC RAX3000M";
---
>       model = "CMCC RAX3000M with USB3SFP";
549,551c549,550
<                       phy-mode = "gmii";
<                       phy-handle = <0x1f>;
<                       phandle = <0x39>;
---
>                       phy-mode = "2500base-x";
>                       managed = "in-band-status";
686c685
<               phys = <0x21 0x03 0x0f 0x04>;
---
>               phys = <0x21 0x03>;
689a689
>               mediatek,u3p-dis-msk = <0x01>;
931c931
< };
---
> };
\ No newline at end of file
```

4. Use `sysupgrade -F` or LuCI to flash the patched firmware

It's normal to get a warning "Image check failed", but "Force upgrade" should work.

## Limitation

Since there are only 2 Ethernet MACs in the MT7981 SoC, If your router uses both of them for WAN and LAN (e.g. CMCC RAX300M), the original eth1 (typically WAN port) will be disabled.

## For OpenWRT Developers / Advanced Users

Please see [this dts patch](https://gist.github.com/cyyself/7d3de89a5b3a063acf5fa2c32f0373dd).

## Notice

[A patch to enable the flow control of the SFP module](https://github.com/openwrt/openwrt/pull/16136) is under review.
