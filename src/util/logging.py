import sys
import logging
from rich.logging import RichHandler
from rich.console import Console

def setup_logging(logToStdout: bool = True):

    # Setup basic logging
    if logToStdout:
        logging.basicConfig(
            level=logging.DEBUG,
            format='[%(filename)s:%(lineno)d] %(message)s',
            handlers=[RichHandler(rich_tracebacks=True, show_path=False, markup=True)]
        )
    else:
        
        stderr_console = Console(file=sys.stderr)

        logging.basicConfig(
            level=logging.DEBUG,
            format='[STDERR] [%(filename)s:%(lineno)d] %(message)s',
            handlers=[RichHandler(rich_tracebacks=True, show_path=False, markup=True, console=stderr_console)],
            force=True
        )
      