from pathlib import Path
import shutil
import os
import subprocess
from time import sleep
import sys
from datetime import datetime
from dateutil import rrule

from tkinter import *
from tkinter import ttk
from tkinter.filedialog import askopenfilename, askdirectory
import tkinter.scrolledtext as st 

root = Tk()
root.title = 'ITTAP'
frm = ttk.Frame(root, padding=20)
frm.grid()

class TkDirSelector:
    '''
    Builder that also contains set of widgets that allow for setting a path.
    '''

    def __init__(
        self,
        row: int = 0,
        label: str = "select directory",
        default_dir: str = "",
    ):
        self.row = row
        self.label = label
        self.default_dir = default_dir
        self.widgets: list = self.create()

    def create(self):
        label = ttk.Label(frm, text=self.label)
        label.grid(column=0, row=self.row)
        ask_dir_button = ttk.Button(frm, text="Choose directory", command=self.update_selection)
        ask_dir_button.grid(column=1, row=self.row)
        ask_dir_selection = ttk.Label(frm, text="")
        ask_dir_selection.grid(column=2, row=self.row)
        return [label, ask_dir_button, ask_dir_selection]

    def update_selection(self):
        directory = askdirectory()
        self.widgets[2].config(text=directory)

def print_user_info(txt: str):
    global scrolled_text
    scrolled_text.insert(INSERT, f"{txt}\n")
    scrolled_text.see(END)

def build_copy_local_command(
    to_path: Path,
):
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

def copy_local(
    to_path: Path,
):
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
    res: list = []
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
    mont_date_out_paths = dict(zip(month_dates, out_paths))
    for d, p in mont_date_out_paths.items():
        print_user_info(p)
        in_files = match_file_substr_multi(
            path_in,
            [
                d.strftime("*_%Y%m*"),
                d.strftime("%Y%m??_*"),
            ],
        )
        for j, infile in enumerate(in_files, 1):
            out_file = p / infile.name
            print_user_info(out_file)
            if not out_file.is_file():
                msg = '{}/{}'.format(str(j), str(len(in_files)))
                print_user_info(msg)
                sleep(0.001)
                shutil.copy(infile, p)
    print_user_info("Files copied successfully!")

if __name__ == '__main__':
    dirselector_raw = TkDirSelector(0, "Raw phone camera pictures directory:")
    dirselector_organized = TkDirSelector(1, "Organized pictures directory:")

    start_date_label = ttk.Label(frm, text="Start date (YYYY-MM-DD):")
    start_date_label.grid(column=0, row=2)
    start_date = Text(frm, height=1, width=15)
    start_date.grid(column=1, row=2)

    copy_button = ttk.Button(
        frm,
        text="Organize Files by Year and Month",
        command = lambda: copy_files(
            path_in = Path(dirselector_raw.widgets[2]['text']),
            path_out = Path(dirselector_organized.widgets[2]['text']),
            start_date = datetime.strptime(start_date.get("1.0",'end-1c'), '%Y-%m-%d'),
            end_date = datetime.now(),
        )
    )
    copy_button.grid(column=0, row=4)

    scrolled_text = st.ScrolledText(frm)
    scrolled_text.grid(column=0, row=5)

    ttk.Button(frm, text="Quit", command=root.destroy).grid(column=0, row=6)
    root.mainloop()

