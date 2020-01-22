#!/usr/bin/python
import argparse
import os
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument("project", help="Name of Project folder")
parser.add_argument("file", help="Name of UI file")
args = parser.parse_args()

try:
    proc_PyUic = subprocess.Popen(["pyuic5", args.file],
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT)
    proc_PyUic.wait()
    out_PyUic = proc_PyUic.stdout.read().decode()
except Exception as ex:
    print("Something went wrong... " + str(ex))

clean_output = out_PyUic.replace(os.environ.get("HOME") + "/Projects/" +
                                 args.project + "/", "")

pyname = args.file.replace(".ui", ".py")

with open("ui_" + pyname, "w") as f:
    f.write(clean_output)

proc_pep = subprocess.Popen(["autopep8", "-i", pyname],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
proc_pep.wait()
print(proc_pep.stdout.read().decode())
