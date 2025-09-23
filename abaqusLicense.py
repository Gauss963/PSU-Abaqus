import subprocess
import time

NEXT_COMMAND = ["sbatch", "/home/gauss112/PSU-Run.slurm"]
REQUIRED_TOKENS = 17

def get_available_abaqus_tokens():
    try:
        output = subprocess.check_output(["/home/gauss112/check-license.sh"], text=True)
    except subprocess.CalledProcessError as e:
        print("Error running check-license.sh:", e)
        return 0

    for line in output.splitlines():
        if "abaqus:" in line:
            parts = line.split()
            try:
                issued = int(parts[2])
                used = int(parts[3])
                return issued - used
            except (IndexError, ValueError) as e:
                print("Parsing error:", e, " line =", parts)
                return 0
    return 0

def main():
    while True:
        available = get_available_abaqus_tokens()
        print(f"Abaqus token available: {available}")
        if available >= REQUIRED_TOKENS:
            print("Token sufficient, executing next command...")
            subprocess.run(NEXT_COMMAND)
            break
        time.sleep(3)

if __name__ == "__main__":
    main()