#!/usr/bin/python
import argparse
import os
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument("project", help="Name of Project folder")
parser.add_argument("file", help="Name of UI file")
args = parser.parse_args()

try:
    pyuic_process = subprocess.Popen(["pyuic5", args.file], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    # Use PyQt5's conversion tool because, it has been more reliable (for me at least) and produces clearer output.
    pyuic_process.wait()
    out_PyUic = pyuic_process.stdout.read().decode()
except Exception as ex:
    print("Something went wrong... " + str(ex))
    exit(1)

clean_output = out_PyUic.replace(os.environ.get("HOME") + "/Projects/" + args.project + "/", "")

py_name = "ui_" + args.file.replace(".ui", ".py")

with open(py_name, "w") as f:
    f.write(clean_output)

pep_process = subprocess.Popen(["autopep8", "--max-line-length=120", "-i", py_name], stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)
pep_process.wait()
print(pep_process.stdout.read().decode())
