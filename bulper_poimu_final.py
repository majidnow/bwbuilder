import argparse, subprocess, shutil, os

# added by poimu
import xml.etree.ElementTree as ET

BW_WORKSPACE="D:/Projects/STM32CubeIDE/workspace_1.15.0"
CDT_DIR="C:/ST/STM32CubeIDE_1.15.0/STM32CubeIDE/headless-build.bat"
RELEAS_DIR="D:/Storage/beachwolf/Archive/Release"
WL_RELEASE_PATH="D:/Storage/wolfloader/Archive/ver 2"
CRC_GEN_PATH=r"D:\Storage\tools\crcc\main.exe"

# BW_WORKSPACE=r"D:\Projects\Programming\STM32CubeIDE\workspace_1.19.0"
# CDT_DIR=r"C:\ST\STM32CubeIDE_1.19.0\STM32CubeIDE\headless-build.bat"
# RELEAS_DIR=r"D:\Data\Storage\beachwolf\Archive\Release"
# WL_RELEASE_PATH=r"D:\Data\Storage\wolfloader\Archive\ver 2"
# CRC_GEN_PATH=r"D:\Data\Storage\tools\bulper-v2\crcc\main.exe"

BW_PROJECT_DIR=BW_WORKSPACE+"/BeachWolf"
# removed by poimu
# SRECORD_DIR=r"C:\Portables\srecord\bin\srec_cat.exe"

VARIATION_LIST=["FC22-01", "FC22-02", "FC22-02-LL", "FC22-03", "FC22R-01", "FC22R-02"]
UPDATE_PATHES_LIST=["S-1", "S-2", "S-2-LL", "S-3", "AR-1", "AR-2", "BL"]

# added by poimu
# False = original preprocessor/build behavior from the base code.
# True  = read preprocessor symbols from BeachWolf/.cproject and optionally
#         select which related Build Configuration(s) should be built.
USE_CPROJECT_PREPROCESSOR_SELECTION = False

# Used only when USE_CPROJECT_PREPROCESSOR_SELECTION is True.
# "ALL" builds all configurations from VARIATION_LIST sequentially.
# Or use exact symbol names found in .cproject, for example:
# SELECTED_PREPROCESSORS = ["FC22_01", "FC22R_02"]
SELECTED_PREPROCESSORS = "ALL"

# added by poimu
# False keeps the original release behavior.
# True creates Firmware.hex = WolfLoader.hex + BeachWolf.hex for programmer use.
# باید مدل  stm32 مشخص شود
# Must be set with true memory map
CREATE_PROGRAMMER_HEX = False

# VARIATION_LIST=["FC22-03", "FC22R-02"]
# UPDATE_PATHES_LIST=["S-3", "AR-2", "BL"]

BLACK   = "\033[30m"
RED     = "\033[31m"
GREEN   = "\033[32m"
YELLOW  = "\033[33m"
BLUE    = "\033[34m"
MAGENTA = "\033[35m"
CYAN    = "\033[36m"
WHITE   = "\033[37m"
RESET   = "\033[0m"

def find_nth(haystack: str, needle: str, n: int) -> int:
    start = haystack.find(needle)
    while start >= 0 and n > 1:
        start = haystack.find(needle, start+len(needle))
        n -= 1
    return start


# added by poimu
# removed by poimu
# def show_progress(percent, stage):
#     """Show script progress in CMD / PowerShell without compiler logs."""
#     print(f"[{percent:3}%] {stage}")

# added by poimu
# For CMD

# removed by poimu
# def show_progress(percent, stage):
#     """Show progress on a single line in CMD / PowerShell."""
#     bar_length = 20
#     filled = int(bar_length * percent / 100)
#     bar = "#" * filled + "-" * (bar_length - filled)
#     print(
#         f"\r[{bar}] {percent:3}% {stage:<32}",
#         end="\n" if percent == 100 else "",
#         flush=True
#     )

# added by poimu
# For PowerShell
def show_progress(percent, stage):
    """Show colored progress on a single line in PowerShell."""
    bar_length = 20
    filled = int(bar_length * percent / 100)
    bar = (
        GREEN + "█" * filled +
        WHITE + "░" * (bar_length - filled) +
        RESET
    )
    print(
        f"\r[{bar}] {YELLOW}{percent:3}%{RESET} {stage:<32}",
        end="\n" if percent == 100 else "",
        flush=True
    )


# added by poimu
def read_cproject_preprocessors(project_dir):
    """Return {build_configuration: [defined symbols]} from CubeIDE .cproject."""
    tree = ET.parse(os.path.join(project_dir, ".cproject"))
    result = {}

    for cconfiguration in tree.getroot().iter("cconfiguration"):
        config_name = None

        for item in cconfiguration.iter():
            if (
                item.tag.endswith("storageModule")
                and item.attrib.get("moduleId") == "org.eclipse.cdt.core.settings"
                and item.attrib.get("name")
            ):
                config_name = item.attrib["name"]
                break

        if not config_name:
            for item in cconfiguration.iter():
                if item.tag.endswith("configuration") and item.attrib.get("name"):
                    config_name = item.attrib["name"]
                    break

        if not config_name or config_name not in VARIATION_LIST:
            continue

        symbols = []
        for option in cconfiguration.iter("option"):
            option_id = option.attrib.get("id", "")
            super_class = option.attrib.get("superClass", "")
            value_type = option.attrib.get("valueType", "")

            if (
                value_type != "definedSymbols"
                and "preprocessor.def.symbols" not in option_id
                and "preprocessor.def.symbols" not in super_class
            ):
                continue

            for value in option.findall("listOptionValue"):
                symbol = value.attrib.get("value")
                if symbol and symbol not in symbols:
                    symbols.append(symbol)

        result[config_name] = symbols

    return result


# added by poimu
def select_variations_from_preprocessors(project_dir):
    preprocessors = read_cproject_preprocessors(project_dir)

    if SELECTED_PREPROCESSORS == "ALL":
        return list(VARIATION_LIST)

    selected = []
    for symbol in SELECTED_PREPROCESSORS:
        matches = [
            variation
            for variation, symbols in preprocessors.items()
            if symbol in symbols
        ]

        # A variation preprocessor must identify exactly one configuration.
        if len(matches) != 1:
            raise ValueError(symbol)

        if matches[0] not in selected:
            selected.append(matches[0])

    return selected


# added by poimu
def read_intel_hex(path):
    """Read Intel HEX and return ({absolute_address: byte}, start_linear_address)."""
    memory = {}
    base_address = 0
    start_linear_address = None

    with open(path, "r", encoding="ascii") as hex_file:
        for line_number, line in enumerate(hex_file, 1):
            line = line.strip()
            if not line:
                continue

            if not line.startswith(":"):
                raise ValueError(f"Invalid HEX line {line_number}")

            try:
                record = bytes.fromhex(line[1:])
            except ValueError as exc:
                raise ValueError(f"Invalid HEX line {line_number}") from exc

            if len(record) < 5 or len(record) != record[0] + 5:
                raise ValueError(f"Invalid HEX line {line_number}")

            if sum(record) & 0xFF:
                raise ValueError(f"Invalid HEX checksum at line {line_number}")

            count = record[0]
            address = (record[1] << 8) | record[2]
            record_type = record[3]
            data = record[4:4 + count]

            if record_type == 0x00:
                absolute_address = base_address + address
                for offset, value in enumerate(data):
                    current_address = absolute_address + offset
                    if current_address in memory and memory[current_address] != value:
                        raise ValueError(f"HEX overlap at 0x{current_address:08X}")
                    memory[current_address] = value

            elif record_type == 0x01:
                break

            elif record_type == 0x02:
                if count != 2:
                    raise ValueError(f"Invalid HEX line {line_number}")
                base_address = int.from_bytes(data, "big") << 4

            elif record_type == 0x04:
                if count != 2:
                    raise ValueError(f"Invalid HEX line {line_number}")
                base_address = int.from_bytes(data, "big") << 16

            elif record_type == 0x05:
                if count != 4:
                    raise ValueError(f"Invalid HEX line {line_number}")
                value = int.from_bytes(data, "big")
                if start_linear_address is not None and start_linear_address != value:
                    raise ValueError("Conflicting HEX start addresses")
                start_linear_address = value

            elif record_type == 0x03:
                # Start Segment Address is not needed by STM32 flash programming.
                continue

            else:
                raise ValueError(f"Unsupported HEX record type 0x{record_type:02X}")

    return memory, start_linear_address


# added by poimu
def make_intel_hex_record(address, record_type, data=b""):
    body = bytes([
        len(data),
        (address >> 8) & 0xFF,
        address & 0xFF,
        record_type
    ]) + data
    checksum = (-sum(body)) & 0xFF
    return ":" + (body + bytes([checksum])).hex().upper()


# added by poimu
def merge_intel_hex(bootloader_path, application_path, output_path):
    boot_memory, boot_start = read_intel_hex(bootloader_path)
    app_memory, app_start = read_intel_hex(application_path)

    memory = dict(boot_memory)
    for address, value in app_memory.items():
        if address in memory and memory[address] != value:
            raise ValueError(f"HEX overlap at 0x{address:08X}")
        memory[address] = value

    # removed by poimu
    # start_address = app_start if app_start is not None else boot_start

    # added by poimu
    start_address = boot_start if boot_start is not None else app_start

    with open(output_path, "w", encoding="ascii", newline="\n") as output:
        addresses = sorted(memory)
        index = 0
        current_upper = None

        while index < len(addresses):
            address = addresses[index]
            upper = address >> 16

            if upper != current_upper:
                output.write(
                    make_intel_hex_record(
                        0,
                        0x04,
                        upper.to_bytes(2, "big")
                    ) + "\n"
                )
                current_upper = upper

            lower = address & 0xFFFF
            data = bytearray([memory[address]])
            index += 1

            while (
                index < len(addresses)
                and addresses[index] == address + len(data)
                and (addresses[index] >> 16) == current_upper
                and len(data) < 16
            ):
                data.append(memory[addresses[index]])
                index += 1

            output.write(make_intel_hex_record(lower, 0x00, bytes(data)) + "\n")

        if start_address is not None:
            output.write(
                make_intel_hex_record(
                    0,
                    0x05,
                    start_address.to_bytes(4, "big")
                ) + "\n"
            )

        output.write(make_intel_hex_record(0, 0x01) + "\n")

# Define the parser
parser = argparse.ArgumentParser(description='Build Helper')

# Declare an argument (`--algo`), saying that the 
# corresponding value should be stored in the `algo` 
# field, and using a default value if the argument 
# isn't given
parser.add_argument('-d', action="store", dest='directory', default=BW_PROJECT_DIR, help='project directory')
parser.add_argument('-v', action="store", dest='version', default=r"\BeachWolf\include\versions.h", help='file that contain version variables')
parser.add_argument('-b', action="store", dest='build', default="12345678", help='which build version variable need to increase', type=int)

# Now, parse the command line arguments and store the 
# values in the `args` variable
args = parser.parse_args()

# added by poimu
BUILD_LOG_PATH = os.path.join(os.getcwd(), "bulper_build.log")
with open(BUILD_LOG_PATH, "wb"):
    pass

# added by poimu
show_progress(0, "Starting")

# stash repository to make sure the compiled code build from the last commit
# added by poimu
show_progress(5, "Checking Git workspace")

# removed by poimu
# stash = subprocess.check_output(["git", "stash"], cwd=args.directory).strip().decode()

# added by poimu
# Strict mode: include untracked files in the Git cleanliness check.
# This is intentionally stricter than the base Bulper behavior; any tracked
# or untracked local change makes the workspace dirty and aborts the build.
stash = subprocess.check_output(["git", "stash", "-u"], cwd=args.directory).strip().decode()
if stash != 'No local changes to save':
    print( "The working directory is NOT clean")
    subprocess.check_output(["git", "stash", "pop"], cwd=args.directory)
    exit(1)


# get commit hash
# added by poimu
show_progress(10, "Reading Git commit")

hash = subprocess.check_output(["git", "describe", "--always"], cwd=args.directory).strip().decode()

# build version increment and set commit hash
current_build_version = 0;
COMMIT_HASH_TOKEN = 'COMMIT_HASH'
BUILD_VERSION_TOKEN = 'REVISION'
VERSION_DIR = ""

# added by poimu
show_progress(15, "Reading version")

with open(args.directory+args.version, 'r+') as f:
   content = f.read()
#    replace commit hash
   start = find_nth(content, COMMIT_HASH_TOKEN, 1)+len(COMMIT_HASH_TOKEN)
   for c in content[start:start+20] :
       if c == '"':
           break
       start += 1
   # removed by poimu
   # end   = content[start:start+10].find('\n')+start
   # f.seek(0)
   # f.write(content[0:start])
   # f.write(str(f'"{hash}"'))

   # added by poimu
   end = content.find('\n', start)
   if end < 0:
       end = len(content)

   hash_end = content.find('"', start + 1, end)
   if hash_end < 0:
       raise ValueError("COMMIT_HASH format is invalid")

   updated_content = content[:start] + f'"{hash}"' + content[hash_end + 1:]
   f.seek(0)
   f.write(updated_content)
   f.truncate()
#    print(len(content))
   start = find_nth(content[end:len(content)], BUILD_VERSION_TOKEN, args.build)+len(BUILD_VERSION_TOKEN)+end
   for c in content[start:start+20] :
       if c >= '0' and c <= '9':
           break
       start += 1
#    f.write(content[end:start])
   end   = content[start:start+10].find('\n')+start
#    print(start, end)
   current_build_version_str = content[start:end]
#    print(current_build_version_str)
#    print(":".join("{:02x}".format(ord(c)) for c in content[start:start+end]))
   current_build_version = int(current_build_version_str)
   print(f"{RED}Build Version: {YELLOW}{current_build_version}, {RED}Commit Hash: {YELLOW}{hash}{RESET}")
   VERSION_DIR = f"{current_build_version}-{hash}"

# added by poimu
show_progress(20, "Waiting for confirmation")

answer = input(f"{YELLOW}Continue? (y/n): {RESET}").strip().lower()
if answer != "y":
    print(f"{RED}Cancelled.{RESET}")
    exit()
print(f"{GREEN}Continuing...{RESET}")

# added by poimu
show_progress(25, "Preparing build")

# build
# Symbols to pass
PREPROCESSOR_SYMBOLS = "-DMAIN_RELEASE"
# Copy existing environment and add USER_CFLAGS
env = os.environ.copy()
env["USER_CFLAGS"] = PREPROCESSOR_SYMBOLS

# added by poimu
# Default mode keeps VARIATION_LIST exactly as the base code.
ACTIVE_VARIATION_LIST = VARIATION_LIST
if USE_CPROJECT_PREPROCESSOR_SELECTION:
    try:
        ACTIVE_VARIATION_LIST = select_variations_from_preprocessors(args.directory)
    except (FileNotFoundError, ET.ParseError, ValueError):
        print("Build failed")
        input()
        exit(1)

ACTIVE_UPDATE_PATHES_LIST = [
    UPDATE_PATHES_LIST[VARIATION_LIST.index(c)] for c in ACTIVE_VARIATION_LIST
]

# create configuration list
# removed by poimu
# build_cmd = [CDT_DIR, '-data', BW_WORKSPACE]
# for c in VARIATION_LIST:
#     build_cmd.append("-cleanBuild")
#     build_cmd.append("BeachWolf/"+c)
# # print(build_cmd)
# result = subprocess.run(build_cmd, capture_output=False, text=False)
#
# if result.returncode > 0:
#     print(f"{RED}Build failed: {YELLOW}{result.args}{RESET}")
#     exit()

# added by poimu
show_progress(30, "Building STM32 configurations")

# added by poimu
with open(BUILD_LOG_PATH, "ab") as build_log:
    if USE_CPROJECT_PREPROCESSOR_SELECTION:
        # CubeIDE configurations are built one by one in optional mode.
        for c in ACTIVE_VARIATION_LIST:
            build_cmd = [
                CDT_DIR, '-data', BW_WORKSPACE,
                '-cleanBuild', "BeachWolf/"+c
            ]
            result = subprocess.run(
                build_cmd,
                stdout=build_log,
                stderr=subprocess.STDOUT,
                text=False
            )
            if result.returncode > 0:
                print("Build failed")
                input()
                exit(1)
    else:
        # Same command structure as the base code; only compiler output is hidden.
        build_cmd = [CDT_DIR, '-data', BW_WORKSPACE]
        for c in VARIATION_LIST:
            build_cmd.append("-cleanBuild")
            build_cmd.append("BeachWolf/"+c)

        result = subprocess.run(
            build_cmd,
            stdout=build_log,
            stderr=subprocess.STDOUT,
            text=False
        )

        if result.returncode > 0:
            print("Build failed")
            input()
            exit(1)

# added by poimu
show_progress(60, "Build completed")

RELEASE_PATH = f"{RELEAS_DIR}/{VERSION_DIR}"
UPDATE_DIR = f"{RELEASE_PATH}/FC22-UPDATE"

# we use bootloader ver 1 for 50 and olders
if current_build_version < 51:
    WL_RELEASE_PATH="D:/Storage/wolfloader/Archive/ver 1"

# add WolfLoader
# added by poimu
show_progress(65, "Packaging WolfLoader")

WL_DES_DIR = f"{RELEASE_PATH}/WolfLoader"
WL_PATH = f"{WL_DES_DIR}/WolfLoader.hex"
os.makedirs(WL_DES_DIR, exist_ok=True)
shutil.copy(f"{WL_RELEASE_PATH}/WolfLoader.hex", 
            f"{WL_PATH}")
shutil.copy(f"{WL_RELEASE_PATH}/update.bin", 
            f"{WL_DES_DIR}/update.bin")
crc = subprocess.check_output([CRC_GEN_PATH, f"{WL_DES_DIR}/update.bin"]).decode()
crc_bytes = int(crc).to_bytes(2, byteorder='little')
with open(f"{WL_DES_DIR}/update.bin", "ab") as update:
    update.write(crc_bytes)

# add WolfLoader to Update path for rev-51 and later
if current_build_version > 50:
    wl_update_dir = f"{UPDATE_DIR}/{UPDATE_PATHES_LIST[-1]}"
    os.makedirs(wl_update_dir, exist_ok=True)
    shutil.copy(f"{WL_DES_DIR}/update.bin", 
                f"{wl_update_dir}/update.bin")

# move outputs to release folder
# removed by poimu
# for c, u in zip(VARIATION_LIST, UPDATE_PATHES_LIST):

# added by poimu
show_progress(70, "Packaging variations")

# added by poimu
_total_variations = len(ACTIVE_VARIATION_LIST)

for _variation_index, (c, u) in enumerate(
    zip(ACTIVE_VARIATION_LIST, ACTIVE_UPDATE_PATHES_LIST),
    start=1
):
    src_dir = f"{BW_PROJECT_DIR}/{c}"
    des_dir = f"{RELEASE_PATH}/{c}"
    # print(src_dir, des_dir)
    os.makedirs(des_dir, exist_ok=True)
    shutil.copy(f"{src_dir}/BeachWolf.hex", 
                f"{des_dir}/BeachWolf.hex")
    shutil.copy(f"{src_dir}/update.bin", 
                f"{des_dir}/update.bin")
    
    # merge WolfLoader and BeachWolf
    # removed by poimu
    # merge_hex_cmd = [SRECORD_DIR, WL_PATH, '-Intel', f"{des_dir}/BeachWolf.hex", '-Intel',
    #                 "-o", f"{des_dir}/Firmware.hex", '-Intel']
    # subprocess.run(merge_hex_cmd, capture_output=False, text=False)

    # removed by poimu
    # if CREATE_PROGRAMMER_HEX:
    #     try:
    #         merge_result = subprocess.run(
    #             [
    #                 SRECORD_DIR,
    #                 WL_PATH, "-Intel",
    #                 f"{des_dir}/BeachWolf.hex", "-Intel",
    #                 "-o", f"{des_dir}/Firmware.hex", "-Intel"
    #             ],
    #             stdout=subprocess.DEVNULL,
    #             stderr=subprocess.DEVNULL,
    #             text=False
    #         )
    #     except OSError:
    #         print("HEX merge failed")
    #         input()
    #         exit(1)
    #
    #     if merge_result.returncode != 0:
    #         print("HEX merge failed")
    #         input()
    #         exit(1)

    # added by poimu
    if CREATE_PROGRAMMER_HEX:
        try:
            merge_intel_hex(
                WL_PATH,
                f"{des_dir}/BeachWolf.hex",
                f"{des_dir}/Firmware.hex"
            )
        except (OSError, ValueError):
            print("HEX merge failed")
            input()
            exit(1)

    # add crc
    crc = subprocess.check_output([CRC_GEN_PATH, f"{des_dir}/update.bin"]).decode()
    print(f"{c} CRC: {crc}")
    crc_bytes = int(crc).to_bytes(2, byteorder='little')
    with open(f"{des_dir}/update.bin", "ab") as update:
        update.write(crc_bytes)

    # copy .bin to Update-Directory for rev-51 and later
    if current_build_version > 50:
        update_dir = f"{UPDATE_DIR}/{u}"
        os.makedirs(update_dir, exist_ok=True)
        shutil.copy(f"{des_dir}/update.bin",
                    f"{update_dir}/update.bin")

    # added by poimu
    # 70..98% is tied to actual completed variation packaging.
    _variation_progress = 70 + int(
        28 * _variation_index / max(1, _total_variations)
    )
    show_progress(
        _variation_progress,
        f"Packaged {c} ({_variation_index}/{_total_variations})"
    )

# added by poimu
show_progress(100, "Release completed")
