# STM32CubeIDE: add $(USER_CFLAGS) to every Build Configuration used by the GUI.
# C: Project Properties > C/C++ Build > Settings > Tool Settings > MCU GCC Compiler > Miscellaneous > Other flags
# C++: Project Properties > C/C++ Build > Settings > Tool Settings > MCU G++ Compiler > Miscellaneous > Other flags

import argparse, subprocess, shutil, os
import re

#added by poimu Runs hex_merge.py.
import sys

#added by poimu Supports CRC verification.
import tempfile

import zipfile
import os

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

#added by poimu Resolves the MAIN_RELEASE Revision define.
def resolve_revision_define_occurrence(version_path):
    with open(version_path, "r", encoding="utf-8") as version_file:
        content = version_file.read()

    pattern = re.compile(
        r"^(\s*#define\s+REVISION\s+)([0-9]+)([^\r\n]*)$"
    )
    matches = []
    main_release_matches = []
    stack = []

    def condition_state(directive, expression):
        expression = expression.strip()
        if directive == "ifdef":
            return expression == "MAIN_RELEASE"
        if directive == "ifndef":
            return False if expression == "MAIN_RELEASE" else None
        if "MAIN_RELEASE" not in expression:
            return None
        compact = re.sub(r"\s+", "", expression)
        if "!defined(MAIN_RELEASE)" in compact or compact.startswith("!MAIN_RELEASE"):
            return False
        return True

    for line in content.splitlines():
        directive = re.match(
            r"^\s*#\s*(ifdef|ifndef|if|elif|else|endif)\b(.*)$",
            line,
        )
        if directive:
            kind = directive.group(1)
            expression = directive.group(2)
            if kind in ("ifdef", "ifndef", "if"):
                state = condition_state(kind, expression)
                stack.append([state, state is True])
            elif kind == "elif" and stack:
                previous_state, taken = stack[-1]
                state = condition_state("if", expression)
                if taken:
                    state = False
                stack[-1] = [state, taken or state is True]
            elif kind == "else" and stack:
                previous_state, taken = stack[-1]
                state = None if previous_state is None else not taken
                stack[-1] = [state, taken or state is True]
            elif kind == "endif" and stack:
                stack.pop()
            continue

        match = pattern.match(line)
        if not match:
            continue

        matches.append(match)
        states = [state for state, _ in stack if state is not None]
        if states and all(states):
            main_release_matches.append(len(matches))

    if not matches:
        raise ValueError("#define REVISION not found")
    if len(matches) == 1:
        return 1
    if len(main_release_matches) == 1:
        return main_release_matches[0]

    current_release = [
        occurrence
        for occurrence, match in enumerate(matches, start=1)
        if int(match.group(2)) >= 51
    ]
    if len(current_release) == 1:
        return current_release[0]

    raise ValueError("Unable to identify the MAIN_RELEASE REVISION define")


def set_revision_define(version_path, occurrence, revision_value):
    with open(version_path, "r+", encoding="utf-8") as version_file:
        content = version_file.read()
        matches = list(re.finditer(
            r"(?m)^(\s*#define\s+REVISION\s+)([0-9]+)([^\r\n]*)$",
            content,
        ))
        if occurrence < 1 or occurrence > len(matches):
            raise ValueError("REVISION define occurrence not found")

        match = matches[occurrence - 1]
        updated = (
            content[:match.start(2)]
            + str(revision_value)
            + content[match.end(2):]
        )
        version_file.seek(0)
        version_file.write(updated)
        version_file.truncate()

parser = argparse.ArgumentParser(description='Build Helper')

parser.add_argument('-d', action="store", dest='directory', default=BW_PROJECT_DIR, help='project directory')
parser.add_argument('-v', action="store", dest='version', default=r"\BeachWolf\include\versions.h", help='file that contain version variables')
parser.add_argument('--revision-value', type=int, required=True)
parser.add_argument('--workspace', default=None)
parser.add_argument('--project-name', default=None)
parser.add_argument('--ide', default=None)
parser.add_argument('--git', default=None)
parser.add_argument('--configuration', action='append', default=[])
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

if args.revision_value < 50:
    with open(BUILD_LOG_PATH, "a", encoding="utf-8") as build_log:
        build_log.write("Revision error: revision must be 50 or greater\n")
    print("Build failed")
    exit(1)

with open(BUILD_LOG_PATH, "a", encoding="utf-8") as build_log:
    build_log.write(f"args.configuration = {args.configuration!r}\n")
    build_log.write(f"args.revision_value = {args.revision_value!r}\n")

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

current_build_version = args.revision_value;
COMMIT_HASH_TOKEN = 'COMMIT_HASH'
VERSION_DIR = ""
revision_path = args.directory + args.version

#added by poimu Reports Revision read.
show_progress(15, "Reading version")

try:
    revision_occurrence = resolve_revision_define_occurrence(revision_path)
except (OSError, ValueError) as exc:
    with open(BUILD_LOG_PATH, "a", encoding="utf-8") as build_log:
        build_log.write(f"Revision error: {exc}\n")
    print("Build failed")
    exit(1)

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

#added by poimu Passes MAIN_RELEASE through USER_CFLAGS.
env = os.environ.copy()
env.pop("USER_CFLAGS", None)
PREPROCESSOR_SYMBOLS = "-DMAIN_RELEASE"
env["USER_CFLAGS"] = PREPROCESSOR_SYMBOLS

#added by poimu Logs USER_CFLAGS.
with open(BUILD_LOG_PATH, "a", encoding="utf-8") as build_log:
    build_log.write(
        f"USER_CFLAGS = {env.get('USER_CFLAGS', '')!r}\n"
    )

#added by poimu Validates selected configurations.
if not args.configuration:
    print("Build failed")
    with open(BUILD_LOG_PATH, "a", encoding="utf-8") as build_log:
        build_log.write("No Build Configuration selected\n")
    exit(1)

if any(c not in VARIATION_LIST for c in args.configuration):
    print("Build failed")
    exit(1)

ACTIVE_VARIATION_LIST = list(dict.fromkeys(args.configuration))
ACTIVE_UPDATE_PATHES_LIST = [
    UPDATE_PATHES_LIST[VARIATION_LIST.index(c)] for c in ACTIVE_VARIATION_LIST
]

#added by poimu Runs the real Revision 50 build and the requested Revision build.
PACKAGE_REVISIONS = [50]
if current_build_version > 50:
    PACKAGE_REVISIONS.append(current_build_version)

RELEASE_ROOT = f"{RELEAS_DIR}/{VERSION_DIR}"
WL_RELEASE_PATH_V2 = WL_RELEASE_PATH
WL_RELEASE_PATH_V1 = WL_RELEASE_PATH_V2
STAGE_DIR = tempfile.mkdtemp(prefix="bulper_release_")

_build_progress_start = 30
_build_progress_end = 60
_build_revision_count = len(PACKAGE_REVISIONS)
_build_variation_count = len(ACTIVE_VARIATION_LIST)

try:
    show_progress(_build_progress_start, "Building STM32 configurations")

    for _revision_index, package_revision in enumerate(PACKAGE_REVISIONS):
        set_revision_define(
            revision_path,
            revision_occurrence,
            package_revision,
        )

        _revision_progress_start = (
            _build_progress_start
            + (_build_progress_end - _build_progress_start)
            * _revision_index // _build_revision_count
        )
        _revision_progress_end = (
            _build_progress_start
            + (_build_progress_end - _build_progress_start)
            * (_revision_index + 1) // _build_revision_count
        )

        with open(BUILD_LOG_PATH, "ab") as build_log:
            build_log.write(
                (f"build_revision = {package_revision}\n").encode("utf-8")
            )
            build_log.flush()

            for _variation_index, c in enumerate(ACTIVE_VARIATION_LIST, start=1):
                build_cmd = [
                    CDT_DIR, '-data', BW_WORKSPACE,
                    '-cleanBuild', GUI_PROJECT_NAME+"/"+c,
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
                    env=env,
                )

                if result.returncode > 0:
                    print(f"Build failed: {c}", flush=True)
                    exit(1)

                src_dir = f"{BW_PROJECT_DIR}/{c}"
                stage_dir = os.path.join(
                    STAGE_DIR,
                    str(package_revision),
                    c,
                )
                os.makedirs(stage_dir, exist_ok=True)
                shutil.copy(
                    f"{src_dir}/BeachWolf.hex",
                    f"{stage_dir}/BeachWolf.hex",
                )
                shutil.copy(
                    f"{src_dir}/update.bin",
                    f"{stage_dir}/update.bin",
                )

                show_progress(
                    _revision_progress_start
                    + int(
                        (_revision_progress_end - _revision_progress_start)
                        * _variation_index
                        / max(1, _build_variation_count)
                    ),
                    f"Built {package_revision}/{c}",
                )

    show_progress(60, "Build completed")
    show_progress(65, "Packaging WolfLoader")
    show_progress(70, "Packaging variations")

    _total_packages = len(PACKAGE_REVISIONS) * len(ACTIVE_VARIATION_LIST)
    _packaged_items = 0

    for package_revision in PACKAGE_REVISIONS:
        RELEASE_PATH = f"{RELEASE_ROOT}/{package_revision}"
        UPDATE_DIR = f"{RELEASE_PATH}/FC22-UPDATE"
        package_wl_release_path = (
            WL_RELEASE_PATH_V1
            if package_revision == 50
            else WL_RELEASE_PATH_V2
        )

        WL_DES_DIR = f"{RELEASE_PATH}/WolfLoader"
        WL_PATH = f"{WL_DES_DIR}/WolfLoader.hex"
        os.makedirs(WL_DES_DIR, exist_ok=True)
        shutil.copy(
            f"{package_wl_release_path}/WolfLoader.hex",
            WL_PATH,
        )
        shutil.copy(
            f"{package_wl_release_path}/update.bin",
            f"{WL_DES_DIR}/update.bin",
        )

        crc = subprocess.check_output(
            [CRC_GEN_PATH, f"{WL_DES_DIR}/update.bin"]
        ).decode()
        crc_bytes = int(crc).to_bytes(2, byteorder='little')
        with open(f"{WL_DES_DIR}/update.bin", "ab") as update:
            update.write(crc_bytes)

        if not verify_appended_crc(f"{WL_DES_DIR}/update.bin"):
            print("CRC verification failed: WolfLoader", flush=True)
            exit(1)

        wl_update_dir = f"{UPDATE_DIR}/{UPDATE_PATHES_LIST[-1]}"
        os.makedirs(wl_update_dir, exist_ok=True)
        shutil.copy(
            f"{WL_DES_DIR}/update.bin",
            f"{wl_update_dir}/update.bin",
        )

        for c, u in zip(ACTIVE_VARIATION_LIST, ACTIVE_UPDATE_PATHES_LIST):
            src_dir = os.path.join(
                STAGE_DIR,
                str(package_revision),
                c,
            )
            des_dir = f"{RELEASE_PATH}/{c}"

            os.makedirs(des_dir, exist_ok=True)
            shutil.copy(
                f"{src_dir}/BeachWolf.hex",
                f"{des_dir}/BeachWolf.hex",
            )
            shutil.copy(
                f"{src_dir}/update.bin",
                f"{des_dir}/update.bin",
            )

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

            crc = subprocess.check_output(
                [CRC_GEN_PATH, f"{des_dir}/update.bin"]
            ).decode()
            print(f"{package_revision}/{c} CRC: {crc}")
            crc_bytes = int(crc).to_bytes(2, byteorder='little')
            with open(f"{des_dir}/update.bin", "ab") as update:
                update.write(crc_bytes)

            if not verify_appended_crc(f"{des_dir}/update.bin"):
                print(f"CRC verification failed: {c}", flush=True)
                exit(1)

            update_dir = f"{UPDATE_DIR}/{u}"
            os.makedirs(update_dir, exist_ok=True)
            shutil.copy(
                f"{des_dir}/update.bin",
                f"{update_dir}/update.bin",
            )

            _packaged_items += 1
            show_progress(
                70 + int(28 * _packaged_items / max(1, _total_packages)),
                f"Packaged {package_revision}/{c}",
            )

    print("CRC presence and validity were verified.", flush=True)
    show_progress(100, "Release completed")
finally:
    set_revision_define(
        revision_path,
        revision_occurrence,
        current_build_version,
    )
    shutil.rmtree(STAGE_DIR, ignore_errors=True)


class ziping:

    def __init__(self, folder_path_1, folder_path_2, output_folder):

        self.folder_path_1 = folder_path_1
        self.folder_path_2 = folder_path_2
        self.output_folder = output_folder


    def find_file(self, path, target_name):

        for root, dirs, files in os.walk(path):

            if target_name in files:
                return os.path.join(root, target_name)

            if target_name in dirs:
                return os.path.join(root, target_name)

        return None



    def get_files(self):

        filse = []

        filse.extend(os.listdir(self.folder_path_1))
        filse.extend(os.listdir(self.folder_path_2))

        return filse



    def create_multiple_zip(
        self,
        main_folder,
        exclude_folder_1,
        exclude_folder_2
    ):


        # پیدا کردن FC22-UPDATE یک بار
        fc22_path = self.find_file(
            os.path.dirname(main_folder),
            "FC22-UPDATE"
        )


        for folder in os.listdir(main_folder):

            folder_path = os.path.join(
                main_folder,
                folder
            )


            if not os.path.isdir(folder_path):
                continue


            if folder == exclude_folder_1:
                continue


            if folder == exclude_folder_2:
                continue



            file_path = self.find_file(
                folder_path,
                "update.bin"
            )


            if not file_path:
                continue



            # ZIP داخل پوشه 50 ساخته می‌شود

            output_zip = os.path.join(
                main_folder,
                folder + ".zip"
            )



            with zipfile.ZipFile(
                output_zip,
                'w',
                zipfile.ZIP_DEFLATED
            ) as zipf:



                # اضافه کردن update.bin

                zipf.write(
                    file_path,
                    arcname=os.path.basename(file_path)
                )



                # اضافه کردن FC22-UPDATE

                if fc22_path:

                    for root, dirs, files in os.walk(fc22_path):

                        for file in files:

                            file_path_2 = os.path.join(
                                root,
                                file
                            )


                            arcname = os.path.relpath(
                                file_path_2,
                                os.path.dirname(fc22_path)
                            )


                            zipf.write(
                                file_path_2,
                                arcname=arcname
                            )



            print(
                folder + ".zip created"
            )




    def create_fc22_zip(self):

        folder_50 = self.folder_path_2


        parent_folder = os.path.dirname(
            folder_50
        )


        folder_50_number = int(
            os.path.basename(folder_50)
        )



        for folder in os.listdir(parent_folder):

            folder_path = os.path.join(
                parent_folder,
                folder
            )


            if not os.path.isdir(folder_path):
                continue



            try:

                folder_number = int(folder)

            except ValueError:

                continue



            if folder_number > folder_50_number:


                fc22_path = self.find_file(
                    folder_path,
                    "FC22-UPDATE"
                )


                if fc22_path:


                    output_zip = os.path.join(
                        folder_path,
                        "FC22-UPDATE.zip"
                    )



                    with zipfile.ZipFile(
                        output_zip,
                        'w',
                        zipfile.ZIP_DEFLATED
                    ) as zipf:


                        for root, dirs, files in os.walk(fc22_path):

                            for file in files:

                                file_path = os.path.join(
                                    root,
                                    file
                                )


                                arcname = os.path.relpath(
                                    file_path,
                                    os.path.dirname(fc22_path)
                                )


                                zipf.write(
                                    file_path,
                                    arcname=arcname
                                )


                    print(
                        "FC22-UPDATE.zip created"
                    )

                    return



        print(
            "FC22-UPDATE not found"
        )



folder_path_2 = os.path.join(
    RELEAS_DIR,
    "50"
)

folder_path_1 = os.path.join(
    folder_path_2,
    "WolfLoader"
)




zipper = ziping(
    folder_path_1,
    folder_path_2,
)



zipper.create_multiple_zip(
    folder_path_2,
    "WolfLoader",
    "FC22-UPDATE"
)



zipper.create_fc22_zip()