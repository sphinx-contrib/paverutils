"""Alternative integration of Sphinx and Paver.

To use this module, import it in your pavement.py file as
``from sphinxcontrib import paverutils``,  then define
option Bundles for "html" and/or "pdf" output using the options
described in the task help.

You can also develop your own tasks by calling ``run_sphinx()``
directly.
"""

from __future__ import print_function

import os
import sys

from cogapp import Cog

from paver.doctools import Includer, _cogsh
from paver.easy import *  # noqa

import sphinx

import textwrap


@task
def html(options):
    """Build HTML documentation using Sphinx.

    This task uses the following options, searching first in the
    "html" then "sphinx" section of the options.

    docroot
      the root under which Sphinx will be working.
      default: docs
    builddir
      directory under the docroot where the resulting files are put.
      default: build
    sourcedir
      directory under the docroot for the source files
      default: (empty string)
    doctrees
      the location of the cached doctrees
      default: $builddir/doctrees
    confdir
      the location of the sphinx conf.py
      default: $sourcedir
    outdir
      the location of the generated output files
      default: $builddir/$builder
    builder
      the name of the sphinx builder to use
      default: html
    force_all
      write all files, not just new and changed
    freshenv
      don't use the saved environment, always read all files
    template_args
      dictionary of values to be passed as name-value pairs to the HTML builder
      default: {}
    config_args
      dictionary of values to be passed as name-value pairs to configuration
      default: {}
    """
    run_sphinx(options, 'html')
    return


@task
def pdf(options):
    """Generate PDF output.

    Use Sphinx to produce LaTeX, then use external tools such as
    TeXLive to convert the .tex file to a PDF.

    This task uses the following options, searching first in the
    "pdf" then "sphinx" section of the options.

    docroot
      the root under which Sphinx will be working.
      default: docs
    builddir
      directory under the docroot where the resulting files are put.
      default: build
    sourcedir
      directory under the docroot for the source files
      default: (empty string)
    doctrees
      the location of the cached doctrees
      default: $builddir/doctrees
    confdir
      the location of the sphinx conf.py
      default: $sourcedir
    outdir
      the location of the generated output files
      default: $builddir/$builder
    force_all
      write all files, not just new and changed
    freshenv
      don't use the saved environment, always read all files
    builder
      the name of the sphinx builder to use
      default: pdf
    pdflatex
      the name of the command to use to make a PDF
      default: pdflatex
    """
    rc = run_sphinx(options, 'pdf')
    if rc:
        print('skipping the rest of the build, sphinx returned', rc)
        return rc
    options.order('pdf')
    pdflatex = options.get('pdflatex', 'pdflatex')
    paths = _get_paths(options)
    outdir = options.get('outdir', paths.builddir / options.builder)
    sh('cd %s; PDFLATEX="%s" make -e' % (outdir, pdflatex))
    return


def _wrap_sphinx(sphinxopts):
    try:
        return sphinx.main(sphinxopts)
    except SystemExit as e:
        return e.code


def run_sphinx(options, *option_sets):
    """Helper function to run sphinx with common options.

    Pass the names of namespaces to be used in the search path
    for options.  The "sphinx" namespace is automatically added
    to the end of the list, so passing (options, 'html') causes
    the options to be configured with a search path of ('html', 'sphinx').
    This lets the caller invoke sphinx with different sets of
    options for different purposes.

    Supported options include:

    docroot
      the root under which Sphinx will be working.
      default: docs
    builddir
      directory under the docroot where the resulting files are put.
      default: build
    sourcedir
      directory under the docroot for the source files
      default: (empty string)
    doctrees
      the location of the cached doctrees
      default: $builddir/doctrees
    confdir
      the location of the sphinx conf.py
      default: $sourcedir
    outdir
      the location of the generated output files
      default: $builddir/$builder
    builder
      the name of the sphinx builder to use
      default: html
    force_all
      write all files, not just new and changed
    freshenv
      don't use the saved environment, always read all files
    quiet
      Suppress all output
    template_args
      dictionary of values to be passed as name-value pairs to the HTML builder
      default: {}
    config_args
      dictionary of values to be passed as name-value pairs to configuration
      default: {}
    warnerror
      Flag indicating that Sphinx warnings should be treated as errors.
      Defaults to False.
    """
    if 'sphinx' not in option_sets:
        option_sets += ('sphinx',)
    kwds = dict(add_rest=False)

    # Set the search order of the options
    options.order(*option_sets, **kwds)

    paths = _get_and_create_paths(options)
    template_args = [
        '-A%s=%s' % (name, value)
        for (name, value) in getattr(options, 'template_args', {}).items()
    ]
    config_args = [
        '-D%s=%s' % (name, value)
        for (name, value) in getattr(options, 'config_args', {}).items()
    ]
    sphinxopts = [
        '',
        '-b', options.get('builder', 'html'),
        '-d', paths.doctrees,
        '-c', paths.confdir,
    ]

    if options.get('force_all', False):
        sphinxopts.append('-a')
    if options.get('freshenv', False):
        sphinxopts.append('-E')
    if options.get('warnerror', False):
        sphinxopts.append('-W')
    if options.get('quiet', False):
        sphinxopts.append('-Q')

    sphinxopts.extend(template_args)
    sphinxopts.extend(config_args)
    sphinxopts.extend([paths.srcdir, paths.outdir])
    rc = dry("sphinx-build %s" % (" ".join(sphinxopts),),
             _wrap_sphinx, sphinxopts)

    options.order()
    return rc


def _get_and_create_paths(options):
    """Retrieves and creates paths needed to run sphinx.

    Returns a Bundle with the required values filled in.
    """
    paths = _get_paths(options)
    paths.builddir.mkdir_p()
    paths.outdir.mkdir_p()
    paths.doctrees.mkdir_p()
    return paths


def _get_paths(options):
    """Retrieves paths needed to run sphinx.

    Returns a Bundle with the required values filled in.
    """
    opts = options

    docroot = path(opts.get('docroot', 'docs'))
    if not docroot.exists():
        raise BuildFailure("Sphinx documentation root (%s) does not exist."
                           % docroot)

    builddir = docroot / opts.get("builddir", ".build")

    srcdir = docroot / opts.get("sourcedir", "")
    if not srcdir.exists():
        raise BuildFailure("Sphinx source file dir (%s) does not exist"
                           % srcdir)

    # Where is the sphinx conf.py file?
    confdir = path(opts.get('confdir', srcdir))

    # Where should output files be generated?
    outdir = opts.get('outdir', '')
    if outdir:
        outdir = path(outdir)
    else:
        outdir = builddir / opts.get('builder', 'html')

    # Where are doctrees cached?
    doctrees = opts.get('doctrees', '')
    if not doctrees:
        doctrees = builddir / "doctrees"
    else:
        doctrees = path(doctrees)

    return Bunch(locals())


def adjust_line_widths(lines, break_lines_at, line_break_mode):
    broken_lines = []
    for l in lines:
        # apparently blank line
        if not l.strip() or len(l) <= break_lines_at:
            broken_lines.append(l)
            continue

        if line_break_mode == 'break':
            while l:
                part, l = l[:break_lines_at], l[break_lines_at:]
                broken_lines.append(part)

        elif line_break_mode == 'wrap':
            broken_lines.extend(
                textwrap.fill(l, width=break_lines_at).splitlines()
            )

        elif line_break_mode == 'wrap-no-breaks':
            broken_lines.extend(
                textwrap.fill(
                    l,
                    width=break_lines_at,
                    break_long_words=False,
                    break_on_hyphens=False,
                ).splitlines()
            )

        elif line_break_mode == 'fill':
            prefix = l[:len(l) - len(l.lstrip())]
            broken_lines.extend(
                textwrap.fill(l, width=break_lines_at,
                              subsequent_indent=prefix).splitlines()
            )

        elif line_break_mode == 'continue':
            while l:
                part, l = l[:break_lines_at], l[break_lines_at:]
                if l:
                    part = part + '\\'
                broken_lines.append(part)

        elif line_break_mode == 'truncate':
            broken_lines.append(l[:break_lines_at])

        else:
            raise ValueError('Unrecognized line_break_mode "%s"'
                             % line_break_mode)

    return broken_lines


def run_script(input_file, script_name,
               interpreter='python',
               include_prefix=True,
               ignore_error=False,
               trailing_newlines=True,
               break_lines_at=0,
               line_break_mode='break',
               adjust_python_for_version=True,
               line_cleanups=[],
               ):
    """Run a script in the context of the input_file's directory,
    return the text output formatted to be included as an rst
    literal text block.

    Arguments:

     input_file
      The name of the file being processed by cog.  Usually passed as
      cog.inFile.

     script_name
       The name of the Python script living in the same directory as
       input_file to be run.  If not using an interpreter, this can be
       a complete command line.  If using an alternate interpreter, it
       can be some other type of file. If the command line is very
       long, this can be a list of parts. They will be displayed
       with backslashes indicating the continuation from line to line,
       but will be joined with a space character into a single string
       to be executed.

     include_prefix=True
       Boolean controlling whether the :: prefix is included.

     ignore_error=False
       Boolean controlling whether errors are ignored.  If not
       ignored, the error is printed to stdout and then the command is
       run *again* with errors ignored so that the output ends up in
       the cogged file.

     trailing_newlines=True
       Boolean controlling whether the trailing newlines are added to
       the output.  If False, the output is passed to rstrip() then
       one newline is added.  If True, newlines are added to the
       output until it ends in 2.

     break_lines_at=0
       Integer indicating the length where lines should be broken and
       continued on the next line.  Defaults to 0, meaning no special
       handling should be done.

     line_break_mode='break'
       Name of mode to break lines.

         break
           Insert a hard break
         continue
           Insert a hard break with a backslash
         wrap
           Use textwrap.fill() to wrap
         wrap-no-breaks
           Use textwrap.fill() without breaking on hyphens
           or long words
         fill
           Use textwrap.fill(), maintaining whitespace prefix
           on subsequent lines
         continue
           Insert a hard break and backslash at the end of
           long lines, continuing on the next
         truncate
           Chop the line at the required width and discard the
           remainder

    adjust_python_for_version=True
      Boolean controlling whether the default `python`
      interpreter setting is changed to `python3` when
      running under python 3.

    line_cleanups=[]
      Process each output line through the cleanups and replace the
      input line with the output values. Each cleanup should be a
      callable that accepts the name of the original input file and
      the line of output produced and returns a replacement string, or
      the original input string if no changes are to be made.

    """
    rundir = path(input_file).dirname()
    if (adjust_python_for_version
            and interpreter == 'python'
            and sys.version_info[0] == 3):
        # Automatically switch to python3 if we're running under
        # python3 ourselves.
        interpreter = 'python3'
    cmd_list = script_name
    if isinstance(script_name, list):
        # We've been given a list, convert it to a string.
        script_name = ' '.join(cmd_list)
    if interpreter:
        cmd = '%(interpreter)s %(script_name)s' % {
            'interpreter': interpreter,
            'script_name': script_name,
        }
    else:
        cmd = script_name
    real_cmd = 'cd %(rundir)s; %(cmd)s 2>&1' % {
        'rundir': rundir,
        'cmd': cmd,
    }
    try:
        print()
        output_text = sh(real_cmd, capture=True, ignore_error=ignore_error)
        print(output_text)
    except Exception as err:
        print('*' * 50)
        print('ERROR run_script(%s) => %s' % (real_cmd, err))
        print('*' * 50)
        output_text = sh(real_cmd, capture=True, ignore_error=True)
        print(output_text)
        print('*' * 50)
        if not ignore_error:
            raise
    if include_prefix:
        response = '\n.. code-block:: none\n\n'
    else:
        response = ''

    # Start building our result list.
    lines = []

    # Add the command we ran to the result.
    if isinstance(cmd_list, list):
        # We were originally given a list, so interpret the
        # parts as already split up. Add the continuation
        # markers to the end.
        if interpreter:
            lines.append('\t$ {} {}'.format(interpreter, cmd_list[0] + ' \\'))
        else:
            lines.append('\t$ {}'.format(cmd_list[0] + ' \\'))
        lines.extend(
            l + ' \\'
            for l in cmd_list[1:-1]
        )
        lines.append(cmd_list[-1])
    else:
        raw_command_line = '\t$ %s' % cmd
        for cleanup in line_cleanups:
            raw_command_line = cleanup(input_file, raw_command_line)
        command_line = adjust_line_widths(
            [raw_command_line],
            break_lines_at - 1 if break_lines_at else 64,
            'continue',
        )
        lines.extend(command_line)

    lines.append('')  # a blank line
    lines.extend(output_text.splitlines())  # the output

    # Clean up the raw output lines.
    clean_lines = []
    for line in lines:
        for cleanup in line_cleanups:
            line = cleanup(input_file, line)
        clean_lines.append(line)
    lines = clean_lines

    # Deal with lines that might be too long
    if break_lines_at:
        lines = adjust_line_widths(lines, break_lines_at, line_break_mode)

    response += '\n\t'.join(lines)
    if trailing_newlines:
        while not response.endswith('\n\n'):
            response += '\n'
    else:
        response = response.rstrip()
        response += '\n'
    return response

# Stuff commonly used symbols into the builtins so we don't have to
# import them in all of the cog blocks where we want to use them.
__builtins__['run_script'] = run_script
#__builtins__['sh'] = sh


# Modified from paver.doctools._runcog
def _runcog(options, files, uncog=False):
    """Common function for the cog and runcog tasks."""
    options.order('cog', 'sphinx', add_rest=True)
    c = Cog()
    if uncog:
        c.options.bNoGenerate = True
    c.options.bReplace = True
    c.options.bDeleteCode = options.get("delete_code", False)
    includedir = options.get('includedir', None)
    if includedir:
        include = Includer(includedir, cog=c,
                           include_markers=options.get("include_markers"))
        # load cog's namespace with our convenience functions.
        c.options.defines['include'] = include
        c.options.defines['sh'] = _cogsh(c)

    c.options.sBeginSpec = options.get('beginspec', '[[[cog')
    c.options.sEndSpec = options.get('endspec', ']]]')
    c.options.sEndOutput = options.get('endoutput', '[[[end]]]')

    basedir = options.get('basedir', None)
    if basedir is None:
        basedir = (path(options.get('docroot', "docs"))
                   / options.get('sourcedir', ""))
    basedir = path(basedir)

    if not files:
        pattern = options.get("pattern", "*.rst")
        if pattern:
            files = basedir.walkfiles(pattern)
        else:
            files = basedir.walkfiles()
    for f in files:
        dry("cog %s" % f, c.processOneFile, f)


@task
@consume_args
def cog(options):
    """Run cog against all or a subset of the input source files.

    Examples::

      $ paver cog PyMOTW/atexit
      $ paver cog PyMOTW/atexit/index.rst
      $ paver cog

    See help on paver.doctools.cog for details on the standard
    options.
    """
    options.order('cog', 'sphinx', add_rest=True)
    # Figure out if we were given a filename or
    # directory, and scan the directory for files
    # if we need to.
    files_to_cog = getattr(options, 'args', [])
    if files_to_cog and os.path.isdir(files_to_cog[0]):
        dir_to_scan = path(files_to_cog[0])
        files_to_cog = list(dir_to_scan.walkfiles(
            options.get("pattern", "*.rst")
        ))
    try:
        _runcog(options, files_to_cog)
    except Exception as err:
        print('ERROR: %s' % err)
        raise
    return
