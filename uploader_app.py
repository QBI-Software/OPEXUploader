import argparse
import csv
import logging
import sys
from os import access, R_OK, mkdir
from os.path import join, expanduser, dirname,split

import wx
from configobj import ConfigObj
from requests.exceptions import ConnectionError

from gui.uploadergui import UploaderGUI, dlgScans, dlgConfig, dlgHelp, dlgIDS, dlgDownloads, dlgReports, dlgLogViewer
from report.report import OPEXReport
from uploader import OPEXUploader
from xnatconnect.XnatConnector import XnatConnector
from xnatconnect.XnatOrganizeFiles import Organizer
from resources.dbquery import DBI


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

    def OnCloseDlg(self, event):
        self.Destroy()

class IdsDialog(dlgIDS):
    def __init__(self, parent):
        super(IdsDialog, self).__init__(parent)
        self.idfile = join(dirname(__file__),'resources', 'incorrectIds.csv')
        self.iddb = join(dirname(__file__), 'resources', 'opexconfig.db')
        self.__loadData()

    def __loadData(self):
        dbi = DBI(self.iddb)
        rownum =0
        for ids in dbi.getIDs():
            self.m_grid1.SetCellValue(rownum, 0, ids[0])
            self.m_grid1.SetCellValue(rownum, 1, ids[1])
            rownum += 1

        # if access(self.idfile, R_OK):
        #     with open(self.idfile, 'rb') as csvfile:
        #         sreader = csv.reader(csvfile, delimiter=',', quotechar='"')
        #         rownum = 0
        #         for row in sreader:
        #             if row[0] == 'INCORRECT':
        #                 continue
        #             self.m_grid1.SetCellValue(rownum, 0, row[0])
        #             self.m_grid1.SetCellValue(rownum, 1, row[1])
        #             rownum += 1
        # resize
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
            # try:
            #     data = self.m_grid1.GetTable()
            #     with open(self.idfile, 'wb') as csvfile:
            #         swriter = csv.writer(csvfile, delimiter=',', quotechar='"')
            #         swriter.writerow([data.GetColLabelValue(0), data.GetColLabelValue(1)])
            #         for rownum in range(0, data.GetRowsCount()):
            #             if not data.IsEmptyCell(rownum, 0):
            #                 swriter.writerow([self.m_grid1.GetCellValue(rownum, 0), self.m_grid1.GetCellValue(rownum, 1)])
            dlg = wx.MessageDialog(self, "IDs file saved", "Incorrect IDs", wx.OK)
            dlg.ShowModal()  # Show it
            dlg.Destroy()
            self.Destroy()
        except Exception as e:
            dlg = wx.MessageDialog(self, e.args[0], "Incorrect IDs", wx.OK)
            dlg.ShowModal()  # Show it
            dlg.Destroy()

    def OnAddRow(self, event):
        self.m_grid1.AppendRows(1, True)

    def OnDeleteRow(self, event):
        # get row pos from event
        pos = event.GetEventUserData()
        self.m_grid1.DeleteRows(pos, 1, True)

    def OnCloseDlg(self, event):
        self.Destroy()


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
        dlg = wx.FileDialog(self, "Choose a config file to load")
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
    def __init__(self, aWxTextCtrl):
        self.out = aWxTextCtrl

    def write(self, string):
        self.out.WriteText(string)


####################################################################################################
class OPEXUploaderGUI(UploaderGUI):
    def __init__(self, parent):
        """
        Load from userhome/.xnat.cfg
        :param parent:
        """
        super(OPEXUploaderGUI, self).__init__(parent)
        self.SetTitle("XNAT Connector App")
        self.SetPosition(wx.Point(100, 100))
        self.SetSize((700, 700))
        self.configfile = join(expanduser('~'), '.xnat.cfg')
        self.configdb = join(dirname(__file__),'resources', 'opexconfig.db')
        self.loaded = self.__loadConfig()
        self.runoptions = self.__loadOptions()
        if self.loaded:
            self.chOptions.SetItems(sorted(self.runoptions.keys()))
            self.dbedit.AppendItems(self.config.keys())
        redir = LogOutput(self.tcResults)
        sys.stdout = redir
        self.m_statusBar1.SetStatusText('Welcome to the Uploader! Help is available from the Menu')
        self.Show()

    def __loadConfig(self):
        if self.configfile is not None and access(self.configfile, R_OK):
            print("Loading config file")
            self.config = ConfigObj(self.configfile, encoding='UTF-8')

            return True
        else:
            raise IOError("Config file not accessible: %s", self.configfile)

    def __loadOptions(self):
        """
        Load options for dropdown
        :return:
        """
        dbi = DBI(self.configdb)
        runoptions = dbi.getRunOptions()
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
            dlg = wx.MessageDialog(self, "Database or project configuration is empty or invalid",
                                   "Connection Config Error", wx.OK)
            dlg.ShowModal()
            dlg.Destroy()
            return (None, None)
        else:
            return (db, proj)

    def getLogFile(self):
        logfile = join(expanduser('~'), 'logs', 'xnatupload.log')
        logdir = split(logfile)[0]
        if not access(logdir, R_OK):
            mkdir(logdir)
        return logfile

    def OnAbout(self, e):
        # A message dialog box with an OK button. wx.OK is a standard ID in wxWidgets.
        dlg = wx.MessageDialog(self, "Uploader for OPEX data to XNAT\n(c)2017 QBI Software", "About OPEX Uploader",
                               wx.OK)
        dlg.ShowModal()  # Show it
        dlg.Destroy()  # finally destroy it when finished.

    def OnHelp(self, e):
        """
        Show the User Help Guide
        :param e:
        :return:
        """
        import markdown
        md = markdown.Markdown()
        md.convertFile('README.md', 'HELP.html')
        # Load to dialog
        dlg = dlgHelp(self)
        dlg.m_htmlWin1.LoadPage('HELP.html')
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

    def OnClose(self, e):
        self.Close(True)  # Close the frame.

    def OnOpen(self, e):
        """ Open a file"""
        # self.dirname = ''
        dlg = wx.DirDialog(self, "Choose a directory containing input files")
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
        dlg = dlgLogViewer(self)
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
                    uploader.runDataUpload(proj, self.dirname, runoption)
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
            finally:  # Processing complete
                uploader.xnatdisconnect()
                logging.info("FINISHED")
                print("FINISHED - see xnatupload.log for details")
                self.m_statusBar1.SetStatusText('Done')


def main():
    app = wx.App(False)
    OPEXUploaderGUI(None)
    app.MainLoop()


# Execute the application
if __name__ == '__main__':
    main()
