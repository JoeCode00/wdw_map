import subprocess

def run(string:str, start_new_session:bool=False, capture_output=True, text=True, check=True) -> str:
    return subprocess.run(string.split(' '), start_new_session=start_new_session, capture_output=capture_output, text=text, check=check).stdout

def run_async(string:str, start_new_session:bool=False) -> subprocess.Popen:
    return subprocess.Popen(string.split(' '), start_new_session=start_new_session)