# -*- coding:latin-1 -*-

import re
import sys
from distutils.msvccompiler import MSVCCompiler, get_build_architecture
import subprocess
import os


compiler = MSVCCompiler()
compiler.initialize()
_fmt_header = ';\n; Definition file of %s\n; Generated by vstools\n;\n'


class DumpbinError(Exception):
    pass

class DumpbinParseError(DumpbinError):
    pass


def find_symbols(dll):
    dumpbin_path = compiler.find_exe('dumpbin.exe')
    try:
        output = subprocess.check_output(
            [dumpbin_path, '/nologo', '/exports', dll],
            universal_newlines=True,
        )
    except subprocess.CalledProcessError as e:
        raise DumpbinError(e.output)

    lines = output.split('\n')

    it = iter(lines)

    found = False
    for line in it:
        if 'name' in line:
            found = True
            break

    if not found:
        raise DumpbinParseError

    next(it)
    next(it)
    next(it)

    symbols = []
    exp = re.compile(r'\w+')

    for line in it:
        if not line.strip():
            break
        symbols.append(exp.findall(line)[3])

    return symbols

def dump_def(dll, def_file=None):
    if not def_file:
        def_file = '%s.def' % os.path.splitext(dll)[0]
    dll_base = os.path.basename(dll)
    with open(def_file, 'w') as f:
        f.write(_fmt_header % dll_base)
        f.write('LIBRARY "%s"\n' % dll_base)
        f.write('EXPORTS\n')
        f.writelines("%s\n" % line for line in find_symbols(dll))

def lib_from_def(def_file, arch=None):
    if not arch:
        arch = get_build_architecture()
        if arch == 'Intel':
            arch = 'x86'
        elif arch == 'Itanium':
            arch = 'IA64'
        else:
            arch = 'x64'
    lib_file = '%s.lib' % os.path.splitext(def_file)[0]
    compiler.spawn([compiler.lib, '/nologo', '/MACHINE:%s' % arch,
                   '/DEF:%s' % def_file, '/OUT:%s' % lib_file])
