#!/usr/bin/env python3

import hashlib
import zlib

# CONFIG
FDT_OFFSET = 1

def patch_dt(orig_dts_string):
    out = []
    # Patch status
    usb_patched = False
    ethernet_patched = False
    # dts scan status
    orig_dts_lines = orig_dts_string.splitlines()
    line_idx = 0
    has_gmac0_symbol = False
    has_gmac1_symbol = False
    path = []
    while line_idx < len(orig_dts_lines):
        line = orig_dts_lines[line_idx]
        if line.strip().endswith('{'):
            path.append(line.strip()[:-1].strip())
            if path != ['/', 'ethernet@15100000', 'mac@1']:
                out.append(line)
        elif line.strip().endswith('};'):
            if path == ['/', 'ethernet@15100000']:
                # at the end of ethernet@15100000, add the mac@1 node
                out.append('		mac@1 {')
                out.append('			compatible = "mediatek,eth-mac";')
                out.append('			reg = <0x01>;')
                out.append('			phy-mode = "2500base-x";')
                out.append('			managed = "in-band-status";')
                out.append('		};')
                ethernet_patched = True
            elif path == ['/', 'usb@11200000']:
                # at the end of usb@11200000, add the mediatek,u3p-dis-msk property
                out.append(f"		mediatek,u3p-dis-msk = <0x01>;")
                usb_patched = True
            elif path == ['/', '__symbols__']:
                # add gmac0 and gmac1 symbols if they are not present
                if not has_gmac0_symbol:
                    out.append('		gmac0 = "/ethernet@15100000/mac@0";')
                if not has_gmac1_symbol:
                    out.append('		gmac1 = "/ethernet@15100000/mac@1";')
            if path != ['/', 'ethernet@15100000', 'mac@1']:
                out.append(line)
            path.pop()
        elif path == ['/', 'usb@11200000']:
            # ignore usb 3.0
            key = line.strip().split(' ')[0]
            if key == 'phys':
                usb_phy_list_l = line.find('<')
                usb_phy_list_r = line.rfind('>')
                usb_phy_list = line[usb_phy_list_l+1:usb_phy_list_r].split()
                assert len(usb_phy_list) == 4, 'usb phys should have 4 entries'
                out.append(f"		phys = <{" ".join(usb_phy_list[:2])}>;")
            elif key != 'mediatek,u3p-dis-msk':
                # ignore mediatek,u3p-dis-msk
                out.append(line)
        elif path == ['/', '__symbols__']:
            # check if gmac0 and gmac1 are present
            if line.strip() == "gmac0 = \"/ethernet@15100000/mac@0\";":
                has_gmac0_symbol = True
            elif line.strip() == "gmac1 = \"/ethernet@15100000/mac@1\";":
                has_gmac1_symbol = True
            out.append(line)
        elif path == ['/']:
            # patch Model
            if line.strip().startswith('model = "'):
                out.append(line.replace("\";", " with USB3SFP\";"))
            else:
                out.append(line)
        elif path != ['/', 'ethernet@15100000', 'mac@1']:
            # ignore all mac@1
            out.append(line)
        line_idx += 1
    if usb_patched and ethernet_patched:
        return "\n".join(out)
    else:
        return None

def get_sha1_string(binary_file):
    sha1 = hashlib.sha1()
    sha1.update(binary_file)
    sha1_hex = sha1.hexdigest()
    assert len(sha1_hex) == 40, "Invalid sha1"
    sha1_32group = [hex(int(sha1_hex[i:i+8], 16))[2:] for i in range(0, len(sha1_hex), 8)]
    return "<0x"+" 0x".join(sha1_32group) + ">"

def get_crc32_string(binary_file):
    crc32 = zlib.crc32(binary_file)
    return f"<0x{crc32:08x}>"

if __name__ == '__main__':
    import sys
    import os
    itb_path = os.path.realpath(sys.argv[1])
    build_dir = os.path.realpath(os.path.dirname(sys.argv[0])) + "/build"
    patched_path = os.path.realpath(sys.argv[2])
    
    # Create build directory
    os.makedirs(build_dir, exist_ok=True)

    # Extract the dtb
    assert os.system(f"dumpimage -T flat_dt -p {FDT_OFFSET} -o {build_dir}/orig.dtb " + itb_path) == 0, "Failed to extract dtb"
    
    # Modify the dtb
    assert os.system(f"dtc -I dtb -O dts -o {build_dir}/orig.dts {build_dir}/orig.dtb 2>/dev/null") == 0, "Failed to extract dts"
    with open(f"{build_dir}/orig.dts", "r") as f:
        orig_dts_string = f.read()
        out = patch_dt(orig_dts_string)
        with open(f"{build_dir}/patched.dts", "w") as f:
            f.write(out)
    
    # Rebuild the dtb
    assert os.system(f"dtc -I dts -O dtb -o {build_dir}/patched.dtb {build_dir}/patched.dts 2>/dev/null") == 0, "Failed to rebuild dtb"
    
    # Check new dtb size
    orig_dtb_size = os.path.getsize(f"{build_dir}/orig.dtb")
    patched_dtb_size = os.path.getsize(f"{build_dir}/patched.dtb")
    assert orig_dtb_size >= patched_dtb_size, "New dtb size is larger than original, unable to patch"
    
    # Resize new dtb
    with open(build_dir + "/patched.dtb", "ab") as f:
        f.write(b"\0" * (orig_dtb_size - patched_dtb_size))
    
    # patch itb fdt header
    assert os.system(f"dtc -I dtb -O dts -o {build_dir}/orig_itb.its {itb_path}") == 0, "Failed to extract itb its"
    orig_dtb_bytes = open(f"{build_dir}/orig.dtb", "rb").read()
    orig_sha1 = get_sha1_string(orig_dtb_bytes)
    orig_crc32 = get_crc32_string(orig_dtb_bytes)
    with open(f"{build_dir}/orig_itb.its", "r") as f:
        orig_itb_its = f.read()
        if orig_itb_its.find(orig_sha1) == -1:
            print("Failed to find sha1 in itb its", file=sys.stderr)
            sys.exit(1)
        if orig_itb_its.find(orig_crc32) == -1:
            print("Failed to find crc32 in itb its", file=sys.stderr)
            sys.exit(1)
        patched_sha1 = get_sha1_string(open(f"{build_dir}/patched.dtb", "rb").read())
        patched_crc32 = get_crc32_string(open(f"{build_dir}/patched.dtb", "rb").read())
        patched_itb_its = orig_itb_its.replace(orig_sha1, patched_sha1).replace(orig_crc32, patched_crc32)
        with open(f"{build_dir}/patched_itb.its", "w") as f:
            f.write(patched_itb_its)

    # Rebuild the itb header
    assert os.system(f"dtc -o {build_dir}/patched_itb.itb {build_dir}/patched_itb.its") == 0, "Failed to rebuild itb"
    
    # patch itb file
    itb_file = bytearray(open(itb_path, "rb").read())
    new_itb_header = open(f"{build_dir}/patched_itb.itb", "rb").read()
    itb_file[0:len(new_itb_header)] = new_itb_header[:]
    new_dtb = open(f"{build_dir}/patched.dtb", "rb").read()
    dtb_offset = itb_file.find(orig_dtb_bytes)
    assert dtb_offset != -1, "Failed to find dtb offset"
    itb_file[dtb_offset:dtb_offset+len(new_dtb)] = new_dtb[:]

    with open(patched_path, "wb") as f:
        f.write(itb_file)
    
    print(f"Patched ITB saved to {patched_path}")
