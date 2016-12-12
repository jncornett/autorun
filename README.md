autorun
=======

Automatigically run shell commands when files change.

use cases
---------

Run `make` whenever a file changes in a C++ project:

    $ autorun $project_dir -- make

Run unit tests whenever a python (.py) file is changed in the current directory:

    $ autorun -i '*.py' . -- nosetests

Lint a javascript source file whenever it changes:

    $ autorun -i '*.js' . -- jshint '%'

Run an expensive compile only after waiting a little bit,
allowing the file events to 'settle':

    $ autorun --latency 5.0 . -- make all

install
-------

In the project directory:

    $ python setup.py install


more help
---------

    $ autorun --help
    usage: autorun [-h] [-i PATTERN] [-x PATTERN] [-l SECONDS] [-q] [--debug]
                   [-L PATH] [-C]
                   path ...

    positional arguments:
      path                  the path to watch (recursive)
      command               remaining position arguments are the command to
                            execute. use '%' to substitute the filename of the
                            change event

    optional arguments:
      -h, --help            show this help message and exit
      -i PATTERN, --include PATTERN
                            glob pattern to include. can be specified more than
                            once
      -x PATTERN, --exclude PATTERN
                            glob pattern to exclude. can be specified more than
                            once
      -l SECONDS, --latency SECONDS
                            latency (in seconds) between runs
      -q, --quiet           set verbosity to a minimum
      --debug               set verbosity very high
      -L PATH, --log-file PATH
                            specify a file to append logs to
      -C, --no-color
