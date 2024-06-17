from pathlib import Path, PurePosixPath 
import shutil
import os
import subprocess
from time import sleep
import sys
from datetime import datetime
from dateutil import rrule

import PySimpleGUI as sg

layout = [
    [sg.Text("Temporary File Directory:"), sg.Input(default_text = str(Path().home() / 'camera'), key="temp_dir")],
    [sg.Button("Copy to temporary directory")],
    [sg.Text("Final File Directory:"), sg.Input(default_text = str(Path().home() / 'organized_pictures'), key="final_dir")],
    [sg.Text("Start Date (YYYY-MM-DD):"), sg.Input(key="start_date")],
    [sg.Button("Copy to final directory")],
    [sg.Exit()],
]

window = sg.Window("Phone Picture Backup", layout)

def run_sg_shell_command(cmd, timeout=None, window=None):
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output = ''
    for line in p.stdout:
        line = line.decode(errors='replace' if (sys.version_info) < (3, 5) else 'backslashreplace').rstrip()
        output += line
        print(line)
        window.Refresh() if window else None
    retval = p.wait(timeout)
    return (retval, output)  

def build_copy_local_command(to_path: Path):
    '''
    Builds the shell copy command used to fetch all the pictures
    from the phone memory using MTP and user id.
    Requires gvfs-mtp package and mount under /run/user/{uid}/gvfs.
    '''
    base_gvfs_path = f"/run/user/{os.getuid()}/gvfs/"
    # Assumes that only one MTP host is available
    mtp_host_name_path = '*'
    host_path = '*'
    camera_path = 'DCIM/Camera/'
    copy_command = 'cp -ur '
    cd_commands = 'cd {} && cd {} && cd {} && cd {}'.format(
        base_gvfs_path,
        mtp_host_name_path,
        host_path,
        camera_path,
    )
    final_command = f"{cd_commands} && {copy_command}. {to_path}"
    return final_command

def copy_local(to_path: Path):
    cmd = build_copy_local_command(to_path)
    os.system(cmd)

def find_files_containing(path, contains):
    l = []
    for p in path.glob(contains):
        if p.is_file():
            l.append(p)
    return l

def match_file_substr_multi(
        path: Path,
        substrings: list,
    ) -> list:
    res = []
    for s in substrings:
        res = res + find_files_containing(path, s)
    return res

def get_month_list(
        start_date: datetime,
        end_date: datetime,
    ) -> list:
    return list(rrule.rrule(rrule.MONTHLY, dtstart=start_date, until=end_date))

def create_folder_paths(
        path_out: Path,
        month_dates: list
    ) -> list:
    paths = []
    for d in month_dates:
        p = path_out / d.strftime('%Y')
        new_folder = d.strftime('%m_%b')
        p.joinpath(new_folder).mkdir(parents=True, exist_ok=True)
        p = p / new_folder
        paths.append(p)
    return paths

def copy_files(
        path_in: Path,
        path_out: Path,
        start_date: datetime,
        end_date: datetime | None = None
    ):
    if not end_date:
        end_date = datetime.now()
    month_dates = get_month_list(start_date, end_date)
    out_paths = create_folder_paths(path_out, month_dates)
    mdop = dict(zip(month_dates, out_paths))
    for d, p in mdop.items():
        sg.Print(p)
        in_files = match_file_substr_multi(
            path_in,
            [
                d.strftime("*_%Y%m*"),
                d.strftime("%Y%m??_*"),
            ],
        )
        for j, infile in enumerate(in_files, 1):
            out_file = p / infile.name
            sg.Print(out_file)
            if not out_file.is_file():
                msg = '{}/{}'.format(str(j), str(len(in_files)))
                sg.Print(msg)
                sleep(0.001)
                shutil.copy(infile, p)

while True:
    event, values = window.read()
    print(event, values)
    if event in (sg.WINDOW_CLOSED, "Exit"):
        break
    if event == 'Copy to temporary directory':
        copy_local_cmd = build_copy_local_command(values['temp_dir'])
        run_sg_shell_command(copy_local_cmd, window=window)
    if event == 'Copy to final directory':
        copy_files(
            path_in = Path(values['temp_dir']),
            path_out = Path(values['final_dir']),
            start_date = datetime.strptime(values['start_date'], '%Y-%m-%d'),
            end_date = datetime.now(),
        )
