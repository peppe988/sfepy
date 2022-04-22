#!/usr/bin/env python
"""
Simple script for testing various SfePy functionality, examples not
covered by tests, and running the tests.

The script just runs the commands specified in its main() using the
`subprocess` module, captures the output and compares one or more key
words to the expected ones.

The output of failed commands is saved to 'test_install.log' file.
"""
import time
from argparse import ArgumentParser, RawDescriptionHelpFormatter
import shlex
import subprocess
import logging
import re

DEBUG_FMT = '*' * 55 + '\n%s\n' + '*' * 55

def _get_logger(filename='test_install.log'):
    """
    Convenience function to set-up output and logging.
    """
    logger = logging.getLogger('test_install.py')
    logger.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    file_handler = logging.FileHandler(filename)
    file_handler.setLevel(logging.DEBUG)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger

logger = _get_logger()

def check_output(cmd):
    """
    Run the specified command and capture its outputs.

    Returns
    -------
    out : tuple
        The (stdout, stderr) output tuple.
    """
    logger.info(cmd)
    args = shlex.split(cmd)

    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = [ii.decode() for ii in p.communicate()]

    return out

def report(out, name, line, item, value, eps=None, return_item=False,
           match_numbers=False):
    """
    Check that `item` at `line` of the output string `out` is equal
    to `value`. If not, print the output.
    """
    try:
        if match_numbers:
            status = out.split('\n')[line]

        else:
            status = out.split('\n')[line].split()

    except IndexError:
        logger.error('  not enough output from command!')
        ok = False

    else:
        try:
            if match_numbers:
                pat = '([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?[jJ]?)'
                matches = re.findall(pat, status)
                status_item = matches[item]

            else:
                status_item = status[item]

            logger.info('  comparing: %s %s', status_item, value)

            if eps is None:
                ok = (status_item == value)

            else:
                try:
                    ok = abs(float(status_item) - float(value)) < eps

                except:
                    ok = False

        except IndexError:
            ok = False

    logger.info('  %s: %s', name, ok)

    if not ok:
        logger.debug(DEBUG_FMT, out)

    if return_item:
        return ok, status[item]

    else:
        return ok

def report2(out, name, items, return_item=False):
    """
    Check that `items` are in the output string `out`.
    If not, print the output.
    """
    ok = True
    for s in items:
        logger.info('  checking: %s', s)
        if s not in out:
            ok = False
            break

    logger.info('  %s: %s', name, ok)

    if not ok:
        logger.debug(DEBUG_FMT, out)

    if return_item:
        return ok, s

    else:
        return ok

def report_tests(out, return_item=False):
    """
    Check that all tests in the output string `out` passed.
    If not, print the output.
    """
    search = re.compile(
        '(?:([0-9]+) failed, )*([0-9]+) passed'
        '(?:, ([0-9]+) warnings)*.* in ([0-9.]+) seconds'
    ).search

    try:
        stats = search(out).groups()
        stats = [stat if stat is not None else '0' for stat in stats]

    except AttributeError:
        stats = '0', '0', '0', '-1'
        ok = False

    ok = stats[0] == '0'

    logger.info('  %s failed, %s passed, %s warnings in %s seconds'
                % tuple(stats))

    if not ok:
        logger.debug(DEBUG_FMT, out)

    if return_item:
        return ok, stats[0]

    else:
        return ok

def main():
    parser = ArgumentParser(description=__doc__,
                            formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('--version', action='version', version='%(prog)s')
    parser.parse_args()

    fd = open('test_install.log', 'w')
    fd.close()

    eok = 0

    t0 = time.time()

    out, err = check_output('python3 ./script/blockgen.py')
    eok += report(out, '...', -2, 1, '...done')

    out, err = check_output('python3 ./script/cylindergen.py')
    eok += report(out, '...', -2, 1, '...done')

    out, err = check_output('python3 ./script/convert_mesh.py meshes/3d/cylinder.vtk out.mesh')
    eok += report(out, '...', -2, 1, '...done')

    out, err = check_output('python3 ./script/tile_periodic_mesh.py -r 2,2 meshes/elements/2_4_2.mesh out-per.mesh')
    eok += report(out, '...', -2, 1, 'done.')

    out, err = check_output('python3 ./script/extract_surface.py meshes/various_formats/octahedron.node -')
    eok += report(out, '...', -2, 0, '1185')

    out, err = check_output('python3 ./simple.py examples/diffusion/poisson.py')
    eok += report(out, '...', -3, 5, '1.173819e-16', eps=1e-15)

    out, err = check_output("""python3 ./simple.py -c "ebc_2 : {'name' : 't2', 'region' : 'Gamma_Right', 'dofs' : {'t.0' : -5.0}}" examples/diffusion/poisson.py""")
    eok += report(out, '...', -3, 5, '2.308051e-16', eps=1e-15)

    out, err = check_output('python3 ./simple.py examples/diffusion/poisson_iga.py')
    eok += report(out, '...', -3, 5, '3.373487e-15', eps=1e-14)

    out, err = check_output('python3 ./simple.py examples/navier_stokes/stokes.py')
    eok += report(out, '...', -3, 5, '1.210678e-13', eps=1e-11)

    out, err = check_output('python3 ./simple.py examples/diffusion/poisson_parametric_study.py')
    eok += report(out, '...', -3, 5, '1.606408e-14', eps=1e-13)

    out, err = check_output('python3 ./simple.py examples/linear_elasticity/its2D_3.py')
    eok += report(out, '...', -24, 5, '3.964886e-12', eps=1e-11)
    eok += report(out, '...', -4, 4, '2.58660e+01', eps=1e-5)

    out, err = check_output('python3 ./simple.py examples/linear_elasticity/linear_elastic.py --format h5')
    eok += report(out, '...', -3, 5, '4.638192e-18', eps=1e-15)

    out, err = check_output('python3 ./extractor.py -d cylinder.h5')
    eok += report(out, '...', -2, 1, '...done')

    out, err = check_output('python3 ./postproc.py -n --no-offscreen -o cylinder.png cylinder.h5')
    eok += report(out, '...', -3, 2, 'cylinder.png...')

    out, err = check_output('python3 ./phonon.py examples/phononic/band_gaps.py')
    eok += report(out, '...', -9, 0, '2.08545116e+08', match_numbers=True)
    eok += report(out, '...', -8, 1, '1.16309223e+11', match_numbers=True)

    out, err = check_output('python3 ./phonon.py examples/phononic/band_gaps.py --phase-velocity')
    eok += report(out, '...', -2, 0, '4189.41229592', match_numbers=True)
    eok += report(out, '...', -2, 1, '2620.55608256', match_numbers=True)

    out, err = check_output('python3 ./phonon.py examples/phononic/band_gaps.py -d')
    eok += report(out, '...', -6, 1, '[0,')

    out, err = check_output('python3 ./phonon.py examples/phononic/band_gaps_rigid.py')
    eok += report(out, '...', -9, 0, '4.58709531e+07', match_numbers=True)
    eok += report(out, '...', -8, 1, '1.13929200e+11', match_numbers=True)

    out, err = check_output('python3 ./simple.py examples/quantum/hydrogen.py')
    eok += report(out, '...', -2, -2, '-0.01913506', eps=1e-4)

    out, err = check_output('python3 ./simple.py examples/homogenization/perfusion_micro.py')
    eok += report2(out, '...', ['computing EpA', 'computing PA_3',
                                'computing GA', 'computing EmA',
                                'computing KA'])

    out, err = check_output('python3 examples/homogenization/rs_correctors.py -n')
    eok += report(out, '...', -2, -1, '1.644e-01', match_numbers=True)

    out, err = check_output('python3 examples/large_deformation/compare_elastic_materials.py -n')
    eok += report(out, '...', -3, 5, '1.068759e-14', eps=1e-13)

    out, err = check_output('python3 examples/linear_elasticity/linear_elastic_interactive.py')
    eok += report(out, '...', -16, 0, '1.62128841139e-14', eps=1e-13)

    out, err = check_output('python3 examples/linear_elasticity/modal_analysis.py')
    eok += report(out, '...', -12, 5, '12142.11470773', eps=1e-13)

    out, err = check_output('python3 examples/multi_physics/thermal_electric.py')
    eok += report(out, '...', -4, 5, '2.612933e-14', eps=1e-13)

    out, err = check_output('python3 examples/diffusion/laplace_refine_interactive.py output')
    eok += report(out, '...', -3, 5, '2.675866e-15', eps=1e-13)

    out, err = check_output('python3 examples/diffusion/laplace_iga_interactive.py -o output-tests')
    eok += report(out, '...', -3, 5, '1.028134e-13', eps=1e-12)

    out, err = check_output('python3 examples/dg/imperative_burgers_1D.py -o output-tests')
    eok += report(out, '...', -3, 3, 'moment_1D_limiter')

    out, err = check_output('mpiexec -n 2 python3 examples/diffusion/poisson_parallel_interactive.py output-parallel -2 --silent -ksp_monitor')
    eok += report(out, '...', -2, 4, '8.021313824020e-07', eps=1e-6)

    out, err = check_output('mpiexec -n 2 python3 examples/multi_physics/biot_parallel_interactive.py output-parallel -2 --silent -ksp_monitor')
    eok += report(out, '...', -2, 4, '3.787214380277e-09', eps=1e-8)

    t1 = time.time()

    out, err = check_output('pytest -v --disable-warnings tests/')
    tok, failed = report_tests(out, return_item=True)
    tok = {True : 'ok', False : 'fail'}[tok]

    t2 = time.time()

    fd = open('test_install_times.log', 'a+')
    fd.write('%s: examples: %.2f [s] (%d), tests: %.2f [s] (%s: %s)\n'
             % (time.ctime(t0), t1 - t0, eok, t2 - t1, tok, failed))
    fd.close()

if __name__ == '__main__':
    main()
