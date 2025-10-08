import argparse, subprocess, shutil, os

BW_WORKSPACE="D:/Projects/STM32CubeIDE/workspace_1.15.0"
BW_PROJECT_DIR=BW_WORKSPACE+"/BeachWolf"
CDT_DIR="C:/ST/STM32CubeIDE_1.15.0/STM32CubeIDE/headless-build.bat"
RELEAS_DIR="D:/Storage/beachwolf/Archive/Release"
VARIATION_LIST=["FC22-01", "FC22-02", "FC22-02-LL", "FC22-03",, "FC22R-01", "FC22R-02"]

def find_nth(haystack: str, needle: str, n: int) -> int:
    start = haystack.find(needle)
    while start >= 0 and n > 1:
        start = haystack.find(needle, start+len(needle))
        n -= 1
    return start

# Define the parser
parser = argparse.ArgumentParser(description='Build Helper')

# Declare an argument (`--algo`), saying that the 
# corresponding value should be stored in the `algo` 
# field, and using a default value if the argument 
# isn't given
parser.add_argument('-d', action="store", dest='directory', default=0, help='project directory')
parser.add_argument('-v', action="store", dest='version', default=0, help='file that contain version variables')
parser.add_argument('-b', action="store", dest='build', default=0, help='which build version variable need to increase', type=int)

# Now, parse the command line arguments and store the 
# values in the `args` variable
args = parser.parse_args()

# stash repository to make sure the compiled code build from the last commit
stash = subprocess.check_output(["git", "stash"], cwd=args.directory).strip().decode()
if stash != 'No local changes to save':
    print( "The working directory is NOT clean")
    subprocess.check_output(["git", "stash", "pop"], cwd=args.directory)
    exit(1)


# get commit hash
hash = subprocess.check_output(["git", "describe", "--always"], cwd=args.directory).strip().decode()

# build version increment and set commit hash
COMMIT_HASH_TOKEN = 'COMMIT_HASH'
BUILD_VERSION_TOKEN = 'BUILD_VERSION'
VERSION_DIR = ""
with open(args.directory+args.version, 'r+') as f:
   content = f.read()
#    replace commit hash
   start = find_nth(content, COMMIT_HASH_TOKEN, 1)+len(COMMIT_HASH_TOKEN)
   for c in content[start:start+20] :
       if c == '"':
           break
       start += 1
   end   = content[start:start+10].find('\n')+start
   f.seek(0)
   f.write(content[0:start])
   f.write(str(f'"{hash}"'))
#    print(len(content))
   start = find_nth(content[end:len(content)], BUILD_VERSION_TOKEN, args.build)+len(BUILD_VERSION_TOKEN)+end
   for c in content[start:start+20] :
       if c >= '0' and c <= '9':
           break
       start += 1
   f.write(content[end:start])
   end   = content[start:start+10].find('\n')+start
#    print(start, end)
   current_build_version_str = content[start:end]
#    print(current_build_version_str)
#    print(":".join("{:02x}".format(ord(c)) for c in content[start:start+end]))
   current_build_version = int(current_build_version_str)
#    f.seek(0)
#    f.write(content[0:start])
   f.write(str(current_build_version+1))
   f.write(content[end:len(content)])
   print(f"Build Version: {current_build_version+1}, Commit Hash: {hash}")
   VERSION_DIR = f"{current_build_version+1}-{hash}"

# build
# create configuration list
build_cmd = [CDT_DIR, '-data', BW_WORKSPACE]
for c in VARIATION_LIST:
    build_cmd.append("-cleanBuild")
    build_cmd.append("BeachWolf/"+c)
# print(build_cmd)
subprocess.run(build_cmd, capture_output=False, text=False)

# move outputs to release folder
for c in VARIATION_LIST:
    src_dir = f"{BW_PROJECT_DIR}/{c}"
    des_dir = f"{RELEAS_DIR}/{VERSION_DIR}/{c}"
    # print(src_dir, des_dir)
    os.makedirs(des_dir, exist_ok=True)
    shutil.copy(f"{src_dir}/BeachWolf.hex", 
                f"{des_dir}/BeachWolf.hex")
    shutil.copy(f"{src_dir}/update.bin", 
                f"{des_dir}/update.bin")
    # add crc
    crc = subprocess.check_output(["../crcc/main.exe", f"{des_dir}/update.bin"]).decode()
    print("CRC:", crc)
    crc_bytes = int(crc).to_bytes(2, byteorder='little')
    with open(f"{des_dir}/update.bin", "ab") as update:
        update.write(crc_bytes)
    




    
