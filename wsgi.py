import sys

path = 'REPLACE WITH app path'
if path not in sys.path:
   sys.path.append(path)

from OPEXReportApp import server as application