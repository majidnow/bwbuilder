import argparse, os, re, sys, tempfile

HEX_DIGITS = re.compile(r"^[0-9A-Fa-f]+$")

def decode_record(line, path, line_number):
    if not line.startswith(":"):
        raise ValueError(f"{path}:{line_number}: record does not start with ':'")

    encoded = line[1:]
    if len(encoded) < 10 or len(encoded) % 2 or not HEX_DIGITS.fullmatch(encoded):
        raise ValueError(f"{path}:{line_number}: malformed hexadecimal record")

    record = bytes.fromhex(encoded)
    count = record[0]

    if len(record) != count + 5:
        raise ValueError(f"{path}:{line_number}: invalid byte count")

    if sum(record) & 0xFF:
        raise ValueError(f"{path}:{line_number}: checksum mismatch")

    address = (record[1] << 8) | record[2]
    record_type = record[3]
    data = record[4:-1]

    return address, record_type, data

def read_intel_hex(path):
    memory = {}
    base_address = 0
    start_segment = None
    start_linear = None
    eof_seen = False

    with open(path, "r", encoding="ascii") as hex_file:
        for line_number, line in enumerate(hex_file, 1):
            line = line.strip()
            if not line:
                continue

            if eof_seen:
                raise ValueError(f"{path}:{line_number}: record found after EOF")

            address, record_type, data = decode_record(line, path, line_number)

            if record_type == 0x00:
                if address + len(data) > 0x10000:
                    raise ValueError(f"{path}:{line_number}: data crosses 64 KiB boundary")

                absolute_address = base_address + address
                for offset, value in enumerate(data):
                    current_address = absolute_address + offset
                    if current_address > 0xFFFFFFFF:
                        raise ValueError(f"{path}:{line_number}: address exceeds 32 bits")
                    if current_address in memory and memory[current_address] != value:
                        raise ValueError(
                            f"{path}:{line_number}: conflicting duplicate byte at "
                            f"0x{current_address:08X}"
                        )
                    memory[current_address] = value

            elif record_type == 0x01:
                if address != 0 or data:
                    raise ValueError(f"{path}:{line_number}: invalid EOF record")
                eof_seen = True

            elif record_type == 0x02:
                if address != 0 or len(data) != 2:
                    raise ValueError(f"{path}:{line_number}: invalid type 02 record")
                base_address = int.from_bytes(data, "big") << 4

            elif record_type == 0x03:
                if address != 0 or len(data) != 4:
                    raise ValueError(f"{path}:{line_number}: invalid type 03 record")
                value = (
                    int.from_bytes(data[:2], "big"),
                    int.from_bytes(data[2:], "big"),
                )
                if start_segment is not None and start_segment != value:
                    raise ValueError(f"{path}:{line_number}: conflicting start segment")
                start_segment = value

            elif record_type == 0x04:
                if address != 0 or len(data) != 2:
                    raise ValueError(f"{path}:{line_number}: invalid type 04 record")
                base_address = int.from_bytes(data, "big") << 16

            elif record_type == 0x05:
                if address != 0 or len(data) != 4:
                    raise ValueError(f"{path}:{line_number}: invalid type 05 record")
                value = int.from_bytes(data, "big")
                if start_linear is not None and start_linear != value:
                    raise ValueError(f"{path}:{line_number}: conflicting start linear address")
                start_linear = value

            else:
                raise ValueError(
                    f"{path}:{line_number}: unsupported HEX record type 0x{record_type:02X}"
                )

    if not eof_seen:
        raise ValueError(f"{path}: missing EOF record")

    return memory, start_segment, start_linear

def make_intel_hex_record(address, record_type, data=b""):
    body = bytes([
        len(data),
        (address >> 8) & 0xFF,
        address & 0xFF,
        record_type,
    ]) + data
    checksum = (-sum(body)) & 0xFF
    return ":" + (body + bytes([checksum])).hex().upper()

def write_intel_hex(memory, start_segment, start_linear, output_path):
    addresses = sorted(memory)
    lines = []
    index = 0
    current_upper = None

    while index < len(addresses):
        address = addresses[index]
        upper = address >> 16

        if upper > 0xFFFF:
            raise ValueError(f"Cannot encode address 0x{address:X}")

        if upper != current_upper:
            lines.append(
                make_intel_hex_record(0, 0x04, upper.to_bytes(2, "big"))
            )
            current_upper = upper

        lower = address & 0xFFFF
        data = bytearray([memory[address]])
        index += 1

        while (
            index < len(addresses)
            and len(data) < 16
            and addresses[index] == address + len(data)
            and (addresses[index] >> 16) == current_upper
        ):
            data.append(memory[addresses[index]])
            index += 1

        lines.append(make_intel_hex_record(lower, 0x00, bytes(data)))

    if start_segment is not None:
        cs, ip = start_segment
        lines.append(
            make_intel_hex_record(
                0,
                0x03,
                cs.to_bytes(2, "big") + ip.to_bytes(2, "big"),
            )
        )

    if start_linear is not None:
        lines.append(
            make_intel_hex_record(0, 0x05, start_linear.to_bytes(4, "big"))
        )

    lines.append(make_intel_hex_record(0, 0x01))

    output_dir = os.path.dirname(os.path.abspath(output_path))
    os.makedirs(output_dir, exist_ok=True)

    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="ascii",
            newline="\n",
            dir=output_dir,
            prefix=os.path.basename(output_path) + ".",
            suffix=".tmp",
            delete=False,
        ) as temp:
            temp.write("\n".join(lines) + "\n")
            temp_path = temp.name

        os.replace(temp_path, output_path)
    except OSError:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
        raise

def merge_intel_hex(bootloader_path, application_path, output_path):
    boot_memory, boot_segment, boot_start = read_intel_hex(bootloader_path)
    app_memory, app_segment, app_start = read_intel_hex(application_path)

    memory = dict(boot_memory)
    identical_overlap = 0

    for address, value in app_memory.items():
        if address in memory:
            if memory[address] != value:
                raise ValueError(
                    f"HEX overlap at 0x{address:08X}: "
                    f"WolfLoader=0x{memory[address]:02X}, BeachWolf=0x{value:02X}"
                )
            identical_overlap += 1
        memory[address] = value

    start_segment = boot_segment if boot_segment is not None else app_segment
    start_linear = boot_start if boot_start is not None else app_start

    write_intel_hex(memory, start_segment, start_linear, output_path)

    check_memory, check_segment, check_start = read_intel_hex(output_path)
    if check_memory != memory:
        os.remove(output_path)
        raise ValueError("HEX merge verification failed: data map changed")
    if check_segment != start_segment or check_start != start_linear:
        os.remove(output_path)
        raise ValueError("HEX merge verification failed: start address changed")

    return identical_overlap

def main():
    parser = argparse.ArgumentParser(description="Strict Intel HEX merger")
    parser.add_argument("bootloader")
    parser.add_argument("application")
    parser.add_argument("-o", "--output", required=True)
    args = parser.parse_args()

    try:
        identical_overlap = merge_intel_hex(
            args.bootloader,
            args.application,
            args.output,
        )
        print(f"HEX merge passed: {identical_overlap} identical overlap byte(s)")
        return 0
    except (OSError, ValueError) as exc:
        print(f"HEX merge failed: {exc}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
