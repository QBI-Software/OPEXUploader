import argparse
import logging
import sys
import threading
import urllib2
from multiprocessing import freeze_support
from os import access, R_OK, mkdir
from os.path import join, expanduser, dirname, split
from shutil import copyfile
import urllib3
import certifi
import markdown
import wx
from configobj import ConfigObj
from requests.exceptions import ConnectionError

from config.dbquery import DBI
from opexreport.report import OPEXReport
from opexuploader.bulk_uploader import BulkUploader
from opexuploader.gui.uploadergui import UploaderGUI, dlgScans, dlgConfig, dlgHelp, dlgIDS, dlgDownloads, dlgReports, \
    dlgLogViewer
from opexuploader.uploader import OPEXUploader
from opexuploader.utils import findResourceDir
from xnatconnect.XnatConnector import XnatConnector
from xnatconnect.XnatOrganizeFiles import Organizer

# Required for dist
freeze_support()
########################################################################
# Threading support
EVT_RESULT_ID = wx.NewId()

#logger = logging.getLogger('opex')
lock = threading.Lock()
event = threading.Event()

def EVT_RESULT(win, func):
    """Define Result Event."""
    win.Connect(-1, -1, EVT_RESULT_ID, func)


class ResultEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""

    def __init__(self, data):
        """Init Result Event."""
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_RESULT_ID)
        self.data = data


class UploadThread(threading.Thread):

    def __init__(self,wxObject,uploader, proj, rootdirname,runoption):
        threading.Thread.__init__(self)
        self.runoption = runoption
        self.wxObject = wxObject
        self.uploader = uploader
        self.proj = proj
        self.rootdirname = rootdirname

        self.setDaemon(True)

        #Test connection
        if not self.uploader.xnat.testconnection():
            wx.PostEvent(self.wxObject, ResultEvent('UploadThread: connection failed'))

    def run(self):
        print('UploadThread: Starting thread run')
        errmsg = None
        try:
            event.set()
            lock.acquire(True)

            if self.runoption == 'bulk':
                bulk = BulkUploader(self.uploader)
                bulk.run(self.proj, self.rootdirname)
                bulk.close()
                print("***BULK LOAD COMPLETED**")
            else:
                self.uploader.runDataUpload(self.proj, self.rootdirname, self.runoption)

        except Exception as e:
            errmsg = "ERROR: %s" % str(e)
            logging.error(errmsg)

        finally:
            lock.release()
            event.clear()
            # Processing complete
            self.uploader.xnatdisconnect()
            if errmsg is None:
                msg = 'FINISHED Upload - see Log for details'
                logging.info(msg)
            else:
                msg = errmsg
            wx.PostEvent(self.wxObject, ResultEvent(msg))




####################################################################################
class DownloadDialog(dlgDownloads):
    def __init__(self, parent, db=None, proj=None):
        super(DownloadDialog, self).__init__(parent)
        self.configfile = parent.configfile
        self.db = db
        self.proj = proj

    def OnCSVDownload(self, event):
        """
        Download CSVs
        :param event:
        :return:
        """
        downloaddirname = self.m_downloaddir.GetPath()
        deltas = self.chDelta.GetValue()
        if downloaddirname is not None and self.db is not None and self.proj is not None:

            xnat = XnatConnector(self.configfile, self.db)
            xnat.connect()
            subjects = xnat.getSubjectsDataframe(self.proj)
            op = OPEXReport(subjects=subjects)
            op.xnat = xnat
            if op.downloadOPEXExpts(self.proj,downloaddirname, deltas):
                msg = "***Downloads Completed: %s" % downloaddirname
                logging.info(msg)
            else:
                msg = "Error during download"
                logging.error(msg)

            dlg = wx.MessageDialog(self, msg, "Download CSVs", wx.OK)
            dlg.ShowModal()  # Show it
            dlg.Destroy()

    def OnGenerateReports(self, event):
        """
        Download CSVs
        :param event:
        :return:
        """
        downloaddirname = self.m_downloaddir.GetPath()
        deltas = self.chDelta.GetValue()
        if downloaddirname is not None and self.db is not None and self.proj is not None:
            self.Destroy()  # close window
            xnat = XnatConnector(self.configfile, self.db)
            xnat.connect()
            subjects = xnat.getSubjectsDataframe(self.proj)
            op = OPEXReport(subjects=subjects)
            op.xnat = xnat
            if op.generateCantabReport(projectcode=self.proj, outputdir=downloaddirname, deltas=True):
                msg = "***CANTAB report Completed: %s" % downloaddirname
                logging.info(msg)
            else:
                msg = "Error during CANTAB report"
                logging.error(msg)

            if op.generateBloodReport(projectcode=self.proj, outputdir=downloaddirname):
                msg = "***BLOOD report Completed: %s" % downloaddirname
                logging.info(msg)
            else:
                msg = "Error during BLOOD report"
                logging.error(msg)

            dlg = wx.MessageDialog(self, msg, "Download CSVs", wx.OK)
            dlg.ShowModal()  # Show it
            dlg.Destroy()


    def OnCloseDlg(self, event):
        self.Destroy()

############################################################################################################
class ReportDialog(dlgReports):
    def __init__(self, parent, db=None, proj=None):
        super(ReportDialog, self).__init__(parent)
        if db is None or proj is None:
            dlg = wx.MessageDialog(self, "XNAT Login details and project required", "Download CSVs", wx.OK)
            dlg.ShowModal()  # Show it
            dlg.Destroy()
        else:
            self.configfile = parent.configfile
            self.db = db
            self.proj = proj


    def OnGenerateReports(self, event):
        """
        Download CSVs
        :param event:
        :return:
        """
        downloaddirname = self.m_downloaddir.GetPath()
        deltas = self.chDelta.GetValue()
        if downloaddirname is not None and self.db is not None and self.proj is not None:
            xnat = XnatConnector(self.configfile, self.db)
            xnat.connect()
            subjects = xnat.getSubjectsDataframe(self.proj)
            if subjects is not None:
                op = OPEXReport(subjects=subjects)
                op.xnat = xnat
                msg = "Generating CANTAB report ..."
                logging.info(msg)
                print(msg)
                if op.generateCantabReport(projectcode=self.proj, outputdir=downloaddirname, deltas=deltas):
                    msg = "***CANTAB report Completed: %s" % downloaddirname
                    logging.info(msg)
                else:
                    msg = "Error during CANTAB report"
                    logging.error(msg)
                print(msg)
                msg = "Generating BLOOD report ..."
                logging.info(msg)
                print(msg)
                if op.generateBloodReport(projectcode=self.proj, outputdir=downloaddirname, deltas=deltas):
                    msg = "***BLOOD report Completed: %s" % downloaddirname
                    logging.info(msg)
                else:
                    msg = "Error during BLOOD report"
                    logging.error(msg)
                print(msg)
            else:
                msg = "Cannot list subjects from XNAT"
                logging.error(msg)
                print(msg)
            #close connection
            op.xnat.conn.disconnect()

    def OnCloseDlg(self, event):
        self.Close()

############################################################################################################
class IdsDialog(dlgIDS):
    def __init__(self, parent):
        super(IdsDialog, self).__init__(parent)
        self.resource_dir = findResourceDir()
        self.idfile = join(self.resource_dir, 'incorrectIds.csv')
        self.iddb = join(self.resource_dir, 'opexconfig.db')
        self.__loadData()

    def __loadData(self):
        dbi = DBI(self.iddb)
        rownum =0
        rows = self.m_grid1.GetTable().GetRowsCount()
        idlist = dbi.getIDs()
        for ids in idlist:
            if rownum >= rows:
                self.m_grid1.AppendRows(1,True)
            self.m_grid1.SetCellValue(rownum, 0, ids[0])
            self.m_grid1.SetCellValue(rownum, 1, ids[1])
            rownum += 1
        self.m_grid1.AutoSizeColumns()
        self.m_grid1.AutoSize()

    def OnSaveIds(self, event):
        try:
            dbi = DBI(self.iddb)
            data = self.m_grid1.GetTable()
            addids = []
            for rownum in range(0, data.GetRowsCount()):
                if not data.IsEmptyCell(rownum, 0):
                    addids.append((self.m_grid1.GetCellValue(rownum, 0), self.m_grid1.GetCellValue(rownum, 1)))
            dbi.addIDs(addids)
            dlg = wx.MessageDialog(self, "IDs file saved", "Incorrect IDs", wx.OK)

        except Exception as e:
            dlg = wx.MessageDialog(self, e.args[0], "Incorrect IDs", wx.OK)

        finally:
            dlg.ShowModal()  # Show it
            dlg.Destroy()
            self.Close()

    def OnAddRow(self, event):
        self.m_grid1.AppendRows(1, True)

    def OnDeleteRow(self, event):
        # get row pos from event
        pos = event.GetEventUserData()
        self.m_grid1.DeleteRows(pos, 1, True)

    def OnCloseDlg(self, event):
        self.Close()

############################################################################################################
class ConfigDialog(dlgConfig):
    def __init__(self, parent):
        super(ConfigDialog, self).__init__(parent)
        self.config = None

    def load(self, configfile):
        if access(configfile, R_OK):
            self.config = ConfigObj(configfile)
            self.chConfig.Clear()
            self.chConfig.AppendItems(self.config.keys())
            self.txtURL.Clear()
            self.txtUser.Clear()
            self.txtPass.Clear()

    def OnConfigText(self, event):
        """
        Add new item
        :param event:
        :return:
        """
        if len(event.GetString()) > 0:
            ref = event.GetString()
            self.chConfig.AppendItems([ref])
            self.config[ref] == {'URL': '', 'USER': '', 'PASS': ''}
            self.txtURL.SetValue(self.config[ref]['URL'])
            self.txtUser.SetValue(self.config[ref]['USER'])
            self.txtPass.SetValue(self.config[ref]['PASS'])

    def OnConfigSelect(self, event):
        """
        Select config ref and load fields
        :param event:
        :return:
        """
        ref = self.chConfig.GetStringSelection()
        if self.config is not None and ref in self.config.keys():
            self.txtURL.SetValue(self.config[ref]['URL'])
            self.txtUser.SetValue(self.config[ref]['USER'])
            self.txtPass.SetValue(self.config[ref]['PASS'])

    def OnLoadConfig(self, event):
        """
        Load values from config file
        :param event:
        :return:
        """
        dlg = wx.FileDialog(self, "Choose a config file to load","",wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)
        if dlg.ShowModal() == wx.ID_OK:
            cfile = str(dlg.GetPath())
            self.load(cfile)
            print('Config file loaded')
        dlg.Destroy()

    def OnSaveConfig(self, event):
        """
        Save values to new or existing config
        :param event:
        :return:
        """
        if self.config is not None:
            self.config = ConfigObj(join(expanduser('~'), '.xnat.cfg'))
            url = self.txtURL.GetValue()
            user = self.txtUser.GetValue()
            passwd = self.txtPass.GetValue()
            self.config[self.chConfig.GetValue()] = {'URL': url, 'USER': user, 'PASS': passwd}
            self.config.write()
            print('Config file updated')

        self.Close()

    def OnRemoveConfig(self, event):
        """
        Remove selected ref
        :param event:
        :return:
        """
        ref = self.chConfig.GetStringSelection()
        if self.config is not None:
            del self.config[ref]
            self.config.write()
            print('Config setting removed')
            self.load(configfile=self.config.filename)


####################################################################################################
class LogOutput():
    """
    http://www.blog.pythonlibrary.org/2009/01/01/wxpython-redirecting-stdout-stderr/
    """
    def __init__(self, aWxTextCtrl):
        self.out = aWxTextCtrl

    def write(self, string):
        try:
            wx.CallAfter(self.out.WriteText,string)

        except Exception as e:
            print('Output console error: ',e.args[0])

class LogViewer(dlgLogViewer):
    def __init__(self,parent):
        super(LogViewer, self).__init__(parent)

    def OnRefresh( self, event ):
        logfile = self.Parent.getLogFile()
        self.tcLog.LoadFile(logfile)


####################################################################################################
class OPEXUploaderGUI(UploaderGUI):
    def __init__(self, parent):
        """
        Load from userhome/.xnat.cfg
        :param parent:
        """
        super(OPEXUploaderGUI, self).__init__(parent)
        self.Bind(wx.EVT_CLOSE, self.OnExit)
        self.SetTitle("OPEX Uploader App")
        self.SetPosition(wx.Point(100, 100))
        self.SetSize((700, 700))
        self.configfile = join(expanduser('~'), '.xnat.cfg')
        self.resource_dir = findResourceDir()
        self.configdb = join(self.resource_dir, 'opexconfig.db')
        self.loaded = self.__loadConfig()
        self.runoptions = self.__loadOptions()
        if self.loaded:
            self.chOptions.SetItems(sorted(self.runoptions.keys()))
            self.dbedit.AppendItems(self.config.keys())
        # # DISPLAY OUTPUT IN WINDOW as stdout
        sys.stdout= LogOutput(self.tcResults)
        # Update status bar from Thread
        EVT_RESULT(self, self.__statusoutput)
        self.m_statusBar1.SetStatusText('Welcome to the Uploader! Help is available from the Menu')
        self.Show()

    def __loadConfig(self):
        if not access(self.configfile, R_OK):
            copyfile(join(self.resource_dir,'xnat.cfg'),self.configfile)
        logging.debug("Loading config file:", self.configfile)
        self.config = ConfigObj(self.configfile, encoding='UTF-8')
        return True

    def __loadOptions(self):
        """
        Load options for dropdown
        :return:
        """
        dbi = DBI(self.configdb)
        runoptions = dbi.getRunOptions()
        runoptions['Visit']='--visit'
        runoptions['Bulk upload'] = '--bulk'
        # config = ConfigObj(optionsfile)
        # if 'options' in config:
        #     runoptions = config['options']
        # else:
        #     runoptions = {'Help': '--h'}
        return runoptions

    def __loadConnection(self):
        db = self.dbedit.GetStringSelection()
        proj = self.projectedit.GetValue()
        if len(db) <= 0 and len(proj) <= 0:
            dlg = wx.MessageDialog(self, "Database or project configuration is empty or invalid", "Connection Config Error", wx.OK)
            dlg.ShowModal()
            dlg.Destroy()
            return (None, None)
        else:
            return (db, proj)

    def __statusoutput(self, msg):
        if msg is not None and msg.data is not None:
            self.m_statusBar1.SetStatusText(msg.data)

    def getLogFile(self):
        logfile = join(expanduser('~'), 'logs', 'xnatupload.log')
        logdir = split(logfile)[0]
        if not access(logdir, R_OK):
            mkdir(logdir)
        return logfile

    def OnAbout(self, e):
        # A message dialog box with an OK button. wx.OK is a standard ID in wxWidgets.
        dlg = wx.MessageDialog(self, "Uploader for OPEX data to XNAT\n(c) 2017 QBI Software\nqbi-dev-admin@uq.edu.au", "About OPEX Uploader",
                               wx.OK)
        dlg.ShowModal()  # Show it
        dlg.Destroy()  # finally destroy it when finished.

    def OnHelp(self, e):
        """
        Show the User Help Guide
        :param e:
        :return:
        """

        resource_dir = findResourceDir()
        projdir = dirname(resource_dir)
        local_readme_url = join(projdir, 'README.md')
        readme_url='https://raw.githubusercontent.com/QBI-Software/OPEXUploader/master/README.md'
        http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())
        mdfile = http.request('GET',readme_url)
        # Write locally
        if sys.platform =='win32':
            flag = 'wb'
        else:
            flag = 'w'
        with open(local_readme_url, flag) as output:
            output.write(mdfile.data)

        help_page = join(resource_dir, 'HELP.html')
        md = markdown.Markdown()
        md.convertFile(local_readme_url, help_page)

        # Load to dialog
        dlg = dlgHelp(self)
        dlg.m_htmlWin1.LoadPage(help_page)
        dlg.Show()


    def OnTest(self, e):
        """
        Test connection is correctly configured
        :param e:
        :return:
        """
        self.tcResults.Clear()
        (db, proj) = self.__loadConnection()
        xnat = XnatConnector(self.configfile, db)
        xnat.connect()
        msg = "Connection to %s for project=%s\n" % (db, proj)
        self.tcResults.AppendText(msg)
        if xnat.testconnection():
            msg = "CONNECTION SUCCESSFUL"
            if xnat.get_project(proj).exists():
                msg += " and Project exists"
            else:
                msg += " but Project DOES NOT exist"
        else:
            msg = "CONNECTION FAILED - please check config"
        self.tcResults.AppendText(msg)


    def OnIds(self, event):
        """
        Configure Incorrect ID list
        :param event:
        :return:
        """
        dlg = IdsDialog(self)
        dlg.ShowModal()
        dlg.Destroy()

    def OnLaunch(self, event):
        """
        Dialog for XnatScans organizer
        :param event:
        :return:
        """
        dlg = dlgScans(self)
        if dlg.ShowModal() == wx.ID_OK:
            scaninput = dlg.txtInputScans.GetPath()
            scanoutput = dlg.txtOutputScans.GetPath()
            ignore = dlg.txtIgnoreScans.GetPath()
            opexid = dlg.chkOPEX.GetValue()
            if len(scaninput) <= 0 or len(scanoutput) <= 0:
                dlg = wx.MessageDialog(self, "Please specify data directories", "Scan organizer", wx.OK)
                dlg.ShowModal()  # Show it
                dlg.Destroy()
            else:
                self.tcResults.AppendText("Running Scans Organizer\n*******\n")
                org = Organizer(scaninput, scanoutput, opexid, ignore)
                if org.run():
                    self.tcResults.AppendText("\n***FINISHED***\n")

    def OnExit(self, e):
        dial = wx.MessageDialog(None, 'Are you sure you want to quit?', 'Question',
                                wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)

        ret = dial.ShowModal()

        if ret == wx.ID_YES:
            self.DestroyChildren()
            self.Destroy()

        else:
            e.Veto()

    def OnOpen(self, e):
        """ Open a file"""
        # self.dirname = ''
        dlg = wx.DirDialog(self, "Choose a directory containing input files","",wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)
        if dlg.ShowModal() == wx.ID_OK:
            self.dirname = '"{0}"'.format(dlg.GetPath())
            self.dirname = dlg.GetPath()
            # self.StatusBar.SetStatusText("Loaded: %s\n" % self.dirname)
            self.inputedit.SetValue(self.dirname)
        dlg.Destroy()

    def OnEditDirname(self, event):
        self.dirname = '"{0}"'.format(event.GetString())
        self.dirname = event.GetString()
        # self.StatusBar.SetStatusText("Input dir: %s\n" % self.dirname)

    def OnDownload(self, event):
        """
        Run downloads
        :param event:
        :return:
        """
        (db, proj) = self.__loadConnection()
        if db is not None and proj is not None:
            dlg = DownloadDialog(self, db, proj)
            dlg.ShowModal()
            dlg.Destroy()

    def OnReport(self, event):
        """
        Run downloads
        :param event:
        :return:
        """
        (db, proj) = self.__loadConnection()
        if db is not None and proj is not None:
            dlg = ReportDialog(self, db, proj)
            dlg.ShowModal()
            dlg.Destroy()

    def OnClearOutput( self, event ):
        """
        Clear data output window
        :param event:
        :return:
        """
        self.tcResults.Clear()

    def OnLog(self, event):
        """
        Load logfile into viewer
        :param event:
        :return:
        """
        dlg = LogViewer(self)
        logfile = self.getLogFile()
        dlg.tcLog.LoadFile(logfile)
        dlg.ShowModal()
        dlg.Destroy()

    def OnSettings(self, event):
        """
        Configure database connection
        :param event:
        :return:
        """
        dlg = ConfigDialog(self)
        dlg.load(self.configfile)
        dlg.ShowModal()
        dlg.Destroy()

    def OnSelectData(self, event):
        """
        On data selection, enable Run
        :param event:
        :return:
        """
        if self.chOptions.GetStringSelection() != 'Select data':
            self.btnRun.Enable(True)
        else:
            self.btnRun.Enable(False)

    def OnSubmit(self, event):
        """
        Run OPEX Uploader
        :param event:
        :return:
        """
        self.tcResults.Clear()
        runoption = self.runoptions.get(self.chOptions.GetValue())[2:]
        if self.cbChecks.GetValue():
            status = 'Running %s [TEST MODE]' % self.chOptions.GetValue()
        else:
            status = 'Running %s' % self.chOptions.GetValue()
        self.m_statusBar1.SetStatusText(status)
        (db, proj) = self.__loadConnection()
        if self.dirname is None or len(self.dirname) <= 0:
            dlg = wx.MessageDialog(self, "Data directory not specified", "OPEX Uploader", wx.OK)
            dlg.ShowModal()  # Show it
            dlg.Destroy()
        else:
            # Load uploader args
            args = argparse.ArgumentParser(prog='OPEX Uploader')
            args.config = join(expanduser('~'), '.xnat.cfg')
            args.database = db
            args.projectcode = proj
            args.create = self.cbCreateSubject.GetValue()
            #args.skiprows = self.cbSkiprows.GetValue()
            args.checks = self.cbChecks.GetValue()
            args.update = self.cbUpdate.GetValue()

            uploader = OPEXUploader(args, self.getLogFile())
            uploader.config()
            uploader.xnatconnect()
            msg = 'Connecting to Server:%s Project:%s' % (uploader.args.database, uploader.args.projectcode)
            logging.info(msg)
            print(msg)

            try:
                if uploader.xnat.testconnection():
                    logging.info("...Connected")
                    print("...Connected")
                    t = UploadThread(self,uploader,proj,self.dirname, runoption)
                    t.start()
                    # uploader.runDataUpload(proj, self.dirname, runoption)
                else:
                    raise ConnectionError('Not connected')


            except IOError as e:
                logging.error(e)
                print("Failed IO:", e)
            except ConnectionError as e:
                logging.error(e)
                print("Failed connection:", e)
            except ValueError as e:
                logging.error(e)
                print("ValueError:", e)
            except Exception as e:
                logging.error(e)
                print("ERROR:", e)
            # finally:  # Processing complete
            #     uploader.xnatdisconnect()
            #     logging.info("FINISHED")
            #     print("FINISHED - see xnatupload.log for details")
            #     self.m_statusBar1.SetStatusText('Done')




##############################################################################
def main():
    app = wx.App(False)
    OPEXUploaderGUI(None)
    app.MainLoop()


# Execute the application
if __name__ == '__main__':
    main()
