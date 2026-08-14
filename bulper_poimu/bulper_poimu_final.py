# STM32CubeIDE: add $(USER_CFLAGS) to every Build Configuration used by the GUI.
# C: Project Properties > C/C++ Build > Settings > Tool Settings > MCU GCC Compiler > Miscellaneous > Other flags
# C++: Project Properties > C/C++ Build > Settings > Tool Settings > MCU G++ Compiler > Miscellaneous > Other flags

import argparse, subprocess, shutil, os

#added by poimu Runs hex_merge.py.
import sys

#added by poimu Supports CRC verification.
import tempfile


BW_WORKSPACE="D:/Projects/STM32CubeIDE/workspace_1.15.0"
CDT_DIR="C:/ST/STM32CubeIDE_1.15.0/STM32CubeIDE/headless-build.bat"
RELEAS_DIR="D:/Storage/beachwolf/Archive/Release"
WL_RELEASE_PATH="D:/Storage/wolfloader/Archive/ver 2"
CRC_GEN_PATH=r"D:\Storage\tools\crcc\main.exe"

BW_PROJECT_DIR=BW_WORKSPACE+"/BeachWolf"

VARIATION_LIST=["FC22-01", "FC22-02", "FC22-02-LL", "FC22-03", "FC22R-01", "FC22R-02"]
UPDATE_PATHES_LIST=["S-1", "S-2", "S-2-LL", "S-3", "AR-1", "AR-2", "BL"]




RED     = "\033[31m"
GREEN   = "\033[32m"
YELLOW  = "\033[33m"
RESET   = "\033[0m"

def find_nth(haystack: str, needle: str, n: int) -> int:
    start = haystack.find(needle)
    while start >= 0 and n > 1:
        start = haystack.find(needle, start+len(needle))
        n -= 1
    return start

#added by poimu Reports GUI progress.
def show_progress(percent, stage):
    print(f"[{percent:3}%] {stage}", flush=True)

#added by poimu Verifies appended CRC.
def verify_appended_crc(bin_path):

    with open(bin_path, "rb") as source:
        data = source.read()

    if len(data) < 2:
        return False

    stored_crc = int.from_bytes(data[-2:], byteorder="little")
    payload = data[:-2]

    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".bin",
        ) as temp:
            temp.write(payload)
            temp_path = temp.name

        calculated_crc = int(
            subprocess.check_output(
                [CRC_GEN_PATH, temp_path]
            ).decode().strip()
        )
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

    return stored_crc == calculated_crc

#added by poimu Resolves Revision profile.
def resolve_revision_occurrence(version_path, revision_profile):

    import re

    with open(version_path, "r", encoding="utf-8") as version_file:
        content = version_file.read()

    matches = list(
        re.finditer(r"\bREVISION\b[^0-9\r\n]*([0-9]+)", content)
    )

    candidates = []
    for occurrence, match in enumerate(matches, start=1):
        revision = int(match.group(1))

        if revision_profile == "50" and revision == 50:
            candidates.append((occurrence, revision))
        elif revision_profile == "51+" and revision >= 51:
            candidates.append((occurrence, revision))

    if len(candidates) != 1:
        raise ValueError(
            f"Revision profile {revision_profile!r} matched "
            f"{len(candidates)} REVISION entries"
        )

    return candidates[0]

parser = argparse.ArgumentParser(description='Build Helper')

parser.add_argument('-d', action="store", dest='directory', default=BW_PROJECT_DIR, help='project directory')
parser.add_argument('-v', action="store", dest='version', default=r"\BeachWolf\include\versions.h", help='file that contain version variables')
parser.add_argument('-b', action="store", dest='build', default="12345678", help='which build version variable need to increase', type=int)

#added by poimu Adds GUI build options.
parser.add_argument(
    '--revision-profile',
    choices=['50', '51+'],
    default=None
)

parser.add_argument('--workspace', default=None)
parser.add_argument('--project-name', default=None)
parser.add_argument('--ide', default=None)
parser.add_argument('--git', default=None)
parser.add_argument('--configuration', action='append', default=[])

parser.add_argument('--define', action='append', default=[])

parser.add_argument('--create-programmer-hex', action='store_true')

args = parser.parse_args()

#added by poimu Applies GUI paths and options.
GUI_PROJECT_NAME = args.project_name or "BeachWolf"
GIT_EXECUTABLE = args.git or "git"
if args.workspace:
    BW_WORKSPACE = args.workspace
if args.ide:
    CDT_DIR = args.ide
BW_PROJECT_DIR = args.directory
CREATE_PROGRAMMER_HEX = args.create_programmer_hex

#added by poimu Creates the build log early.
BUILD_LOG_PATH = os.path.join(os.getcwd(), "bulper_build.log")
with open(BUILD_LOG_PATH, "wb"):
    pass

#added by poimu Resolves selected Revision.
if args.revision_profile:
    try:
        revision_path = args.directory + args.version
        args.build, selected_revision_value = resolve_revision_occurrence(
            revision_path,
            args.revision_profile
        )
    except (OSError, ValueError) as exc:
        with open(BUILD_LOG_PATH, "a", encoding="utf-8") as build_log:
            build_log.write(f"Revision resolution failed: {exc}\n")
        print("Build failed")
        exit(1)
else:
    selected_revision_value = None

#added by poimu Logs build options.
with open(BUILD_LOG_PATH, "a", encoding="utf-8") as build_log:
    build_log.write(f"args.configuration = {args.configuration!r}\n")

    build_log.write(f"args.define = {args.define!r}\n")

    build_log.write(
        f"args.revision_profile = {args.revision_profile!r}\n"
    )
    build_log.write(
        f"revision_occurrence = {args.build!r}\n"
    )
    build_log.write(
        f"selected_revision_value = {selected_revision_value!r}\n"
    )

#added by poimu Reports startup.
show_progress(0, "Starting")

#added by poimu Reports Git check.
show_progress(5, "Checking Git workspace")

stash = subprocess.check_output(
    [GIT_EXECUTABLE, "stash"],
    cwd=args.directory
).strip().decode()
if stash != 'No local changes to save':
    print( "The working directory is NOT clean")

    subprocess.check_output([GIT_EXECUTABLE, "stash", "pop"], cwd=args.directory)
    exit(1)

#added by poimu Reports Commit Hash.
show_progress(10, "Reading Git commit")

hash = subprocess.check_output([GIT_EXECUTABLE, "describe", "--always"], cwd=args.directory).strip().decode()

current_build_version = 0;
COMMIT_HASH_TOKEN = 'COMMIT_HASH'
BUILD_VERSION_TOKEN = 'REVISION'
VERSION_DIR = ""

#added by poimu Reports Revision read.
show_progress(15, "Reading version")

with open(args.directory+args.version, 'r+') as f:
   content = f.read()

   start = find_nth(content, COMMIT_HASH_TOKEN, 1)+len(COMMIT_HASH_TOKEN)
   for c in content[start:start+20] :
       if c == '"':
           break
       start += 1

   end   = content[start:start+10].find('\n')+start
   f.seek(0)
   f.write(content[0:start])
   f.write(str(f'"{hash}"'))

   #added by poimu Uses selected Revision.
   if selected_revision_value is not None:
       current_build_version = selected_revision_value
   else:
       start = (
           find_nth(
               content[end:len(content)],
               BUILD_VERSION_TOKEN,
               args.build
           )
           + len(BUILD_VERSION_TOKEN)
           + end
       )
       for c in content[start:start+20]:
           if c >= '0' and c <= '9':
               break
           start += 1
       end = content[start:start+10].find('\n') + start
       current_build_version_str = content[start:end]
       current_build_version = int(current_build_version_str)
   print(f"{RED}Build Version: {YELLOW}{current_build_version}, {RED}Commit Hash: {YELLOW}{hash}{RESET}")
   VERSION_DIR = f"{current_build_version}-{hash}"

#added by poimu Reports confirmation.
show_progress(20, "Waiting for confirmation")
answer = input(
    f"{YELLOW}Continue? (y/n): {RESET}"
).strip().lower()
if answer != "y":
    print(f"{RED}Cancelled.{RESET}")
    exit()
print(f"{GREEN}Continuing...{RESET}")

#added by poimu Reports build setup.
show_progress(25, "Preparing build")

#added by poimu Passes defines through USER_CFLAGS.
env = os.environ.copy()
env.pop("USER_CFLAGS", None)

PREPROCESSOR_SYMBOLS = " ".join(
    f"-D{symbol}" for symbol in args.define
)
if PREPROCESSOR_SYMBOLS:
    env["USER_CFLAGS"] = PREPROCESSOR_SYMBOLS

#added by poimu Logs USER_CFLAGS.
with open(BUILD_LOG_PATH, "a", encoding="utf-8") as build_log:
    build_log.write(
        f"USER_CFLAGS = {env.get('USER_CFLAGS', '')!r}\n"
    )

#added by poimu Validates selected configurations.
ACTIVE_VARIATION_LIST = VARIATION_LIST
if args.configuration:
    if any(c not in VARIATION_LIST for c in args.configuration):
        print("Build failed")
        exit(1)
    ACTIVE_VARIATION_LIST = list(dict.fromkeys(args.configuration))

ACTIVE_UPDATE_PATHES_LIST = [
    UPDATE_PATHES_LIST[VARIATION_LIST.index(c)] for c in ACTIVE_VARIATION_LIST
]

#added by poimu Runs silent builds and logs compiler output.
show_progress(30, "Building STM32 configurations")

with open(BUILD_LOG_PATH, "ab") as build_log:

    if args.configuration:

        for c in ACTIVE_VARIATION_LIST:
            build_cmd = [
                CDT_DIR, '-data', BW_WORKSPACE,
            ]

            build_cmd += [

                '-cleanBuild', GUI_PROJECT_NAME+"/"+c
            ]

            build_log.write(
                ("build_cmd = " + repr(build_cmd) + "\n").encode("utf-8")
            )
            build_log.flush()

            result = subprocess.run(
                build_cmd,
                stdout=build_log,
                stderr=subprocess.STDOUT,
                text=False,

                env=env
            )

            if result.returncode > 0:
                print(f"Build failed: {c}", flush=True)
                exit(1)

    else:

        build_cmd = [CDT_DIR, '-data', BW_WORKSPACE]

        for c in VARIATION_LIST:
            build_cmd.append("-cleanBuild")

            build_cmd.append(GUI_PROJECT_NAME+"/"+c)

        build_log.write(
            ("build_cmd = " + repr(build_cmd) + "\n").encode("utf-8")
        )
        build_log.flush()

        result = subprocess.run(
            build_cmd,
            stdout=build_log,
            stderr=subprocess.STDOUT,
            text=False,

            env=env
        )

        if result.returncode > 0:
            print("Build failed")
            exit(1)

#added by poimu Reports build completion.
show_progress(60, "Build completed")

RELEASE_PATH = f"{RELEAS_DIR}/{VERSION_DIR}"
UPDATE_DIR = f"{RELEASE_PATH}/FC22-UPDATE"

if current_build_version < 51:
    WL_RELEASE_PATH="D:/Storage/wolfloader/Archive/ver 1"

#added by poimu Reports WolfLoader packaging.
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

#added by poimu Verifies WolfLoader CRC.
if not verify_appended_crc(f"{WL_DES_DIR}/update.bin"):
    print("CRC verification failed: WolfLoader", flush=True)
    exit(1)

if current_build_version > 50:
    wl_update_dir = f"{UPDATE_DIR}/{UPDATE_PATHES_LIST[-1]}"
    os.makedirs(wl_update_dir, exist_ok=True)
    shutil.copy(f"{WL_DES_DIR}/update.bin",
                f"{wl_update_dir}/update.bin")

#added by poimu Packages selected variations.
show_progress(70, "Packaging variations")

_total_variations = len(ACTIVE_VARIATION_LIST)

for _variation_index, (c, u) in enumerate(
    zip(ACTIVE_VARIATION_LIST, ACTIVE_UPDATE_PATHES_LIST),
    start=1
):
    src_dir = f"{BW_PROJECT_DIR}/{c}"
    des_dir = f"{RELEASE_PATH}/{c}"

    os.makedirs(des_dir, exist_ok=True)
    shutil.copy(f"{src_dir}/BeachWolf.hex",
                f"{des_dir}/BeachWolf.hex")
    shutil.copy(f"{src_dir}/update.bin",
                f"{des_dir}/update.bin")

    #added by poimu Creates Firmware.hex with hex_merge.py.
    if CREATE_PROGRAMMER_HEX:
        merge_script = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "hex_merge.py"
        )
        if not os.path.isfile(merge_script):
            print("HEX merge failed: hex_merge.py not found", flush=True)
            exit(1)
        try:
            merge_result = subprocess.run(
                [
                    sys.executable,
                    merge_script,
                    WL_PATH,
                    f"{des_dir}/BeachWolf.hex",
                    "-o",
                    f"{des_dir}/Firmware.hex",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
        except OSError as exc:
            print(f"HEX merge failed: {exc}", flush=True)
            exit(1)
        if merge_result.returncode != 0:
            detail = merge_result.stdout.strip()
            print(detail or "HEX merge failed", flush=True)
            exit(1)

    crc = subprocess.check_output([CRC_GEN_PATH, f"{des_dir}/update.bin"]).decode()
    print(f"{c} CRC: {crc}")
    crc_bytes = int(crc).to_bytes(2, byteorder='little')
    with open(f"{des_dir}/update.bin", "ab") as update:
        update.write(crc_bytes)

    #added by poimu Verifies variation CRC.
    if not verify_appended_crc(f"{des_dir}/update.bin"):
        print(f"CRC verification failed: {c}", flush=True)
        exit(1)

    if current_build_version > 50:
        update_dir = f"{UPDATE_DIR}/{u}"
        os.makedirs(update_dir, exist_ok=True)
        shutil.copy(f"{des_dir}/update.bin",
                    f"{update_dir}/update.bin")

    #added by poimu Updates packaging progress.
    _variation_progress = 70 + int(
        28 * _variation_index / max(1, _total_variations)
    )
    show_progress(
        _variation_progress,
        f"Packaged {c} ({_variation_index}/{_total_variations})"
    )

#added by poimu Reports CRC verification.
print("CRC presence and validity were verified.", flush=True)

#added by poimu Reports Release completion.
show_progress(100, "Release completed")