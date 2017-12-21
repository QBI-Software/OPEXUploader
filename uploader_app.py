import argparse
import logging
import sys
from os import access, R_OK, getcwd
from os.path import join, expanduser

import wx
from configobj import ConfigObj
from requests.exceptions import ConnectionError

from gui.noname import UploaderGUI, dlgScans, dlgConfig
from report.report import OPEXReport
from uploader import OPEXUploader
from xnatconnect.XnatConnector import XnatConnector
from xnatconnect.XnatOrganizeFiles import Organizer


class ConfigDialog(dlgConfig):
    def __init__(self, parent):
        super(ConfigDialog, self).__init__(parent)
        self.config= None

    def load(self, configfile):
        if access(configfile,R_OK):
            self.config = ConfigObj(configfile)
            self.chConfig.Clear()
            self.chConfig.AppendItems(self.config.keys())
            self.txtURL.Clear()
            self.txtUser.Clear()
            self.txtPass.Clear()

    def OnConfigText( self, event ):
        """
        Add new item
        :param event:
        :return:
        """
        if len(event.GetString()) > 0:
            ref=event.GetString()
            self.chConfig.AppendItems([ref])
            self.config[ref]== {'URL': '', 'USER': '', 'PASS': ''}
            self.txtURL.SetValue(self.config[ref]['URL'])
            self.txtUser.SetValue(self.config[ref]['USER'])
            self.txtPass.SetValue(self.config[ref]['PASS'])

    def OnConfigSelect( self, event ):
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

    def OnLoadConfig( self, event ):
        """
        Load values from config file
        :param event:
        :return:
        """
        dlg = wx.FileDialog(self, "Choose a config file to load")
        if dlg.ShowModal() == wx.ID_OK:
            cfile = str(dlg.GetPath())
            self.load(cfile)
            print 'Config file loaded'
        dlg.Destroy()

    def OnSaveConfig( self, event ):
        """
        Save values to new or existing config
        :param event:
        :return:
        """
        if self.config is not None:
            self.config = ConfigObj(join(expanduser('~'),'.xnat.cfg'))
            url = self.txtURL.GetValue()
            user = self.txtUser.GetValue()
            passwd =self.txtPass.GetValue()
            self.config[self.chConfig.GetValue()] = {'URL': url, 'USER': user, 'PASS': passwd}
            self.config.write()
            print 'Config file updated'

        self.Close()

    def OnRemoveConfig( self, event ):
        """
        Remove selected ref
        :param event:
        :return:
        """
        ref = self.chConfig.GetStringSelection()
        if self.config is not None:
            del self.config[ref]
            self.config.write()
            print 'Config setting removed'
            self.load(configfile=self.config.filename)

####################################################################################################
class LogOutput():
    def __init__(self,aWxTextCtrl):
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
        self.SetPosition(wx.Point(100,100))
        self.SetSize((700, 700))
        self.runoptions = self.__loadOptions()
        self.configfile = join(expanduser('~'), '.xnat.cfg')
        self.loaded = self.__loadConfig()
        if self.loaded:
            self.chOptions.SetItems(self.runoptions.keys())
            self.dbedit.AppendItems(self.config.keys())
        redir = LogOutput(self.tcResults)
        sys.stdout = redir
        sys.stderr = redir
        #print 'test'
        self.Show()

    def __loadConfig(self):
        if self.configfile is not None and access(self.configfile, R_OK):
            print("Loading config file")
            self.config = ConfigObj(self.configfile, encoding='UTF-8')

            return True
        else:
            raise IOError("Config file not accessible: %s", self.configfile)

    def __loadOptions(self):
        optionsfile = join('resources','run_options.cfg')
        config = ConfigObj(optionsfile)
        if 'options' in config:
            runoptions = config['options']
        else:
            runoptions = {'Help':'--h'}
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
            return (db,proj)

    def OnAbout(self, e):
        # A message dialog box with an OK button. wx.OK is a standard ID in wxWidgets.
        dlg = wx.MessageDialog(self, "Uploader for OPEX data to XNAT\n(c)2017 QBI Software", "About OPEX Uploader", wx.OK)
        dlg.ShowModal()  # Show it
        dlg.Destroy()  # finally destroy it when finished.

    def OnHelp(self,e):
        self.tcResults.Clear()
        #cmd = self.__loadCommand(['--h'])
        try:
            #output = subprocess.check_output(cmd, shell=True)
            with open('README.md') as f:
                output = f.readlines()
                for line in output:
                    self.tcResults.AppendText(line)
        # except subprocess.CalledProcessError as e:
        #     msg = "Program Execution failed:" + e.message + "(" + str(e.returncode) + ")"
        #     print >> sys.stderr, msg
            #self.tcResults.AppendText(msg)
        except IOError as e:
            msg = "Help file not accessible"
            print >> sys.stderr, msg

    def OnTest(self,e):
        """
        Test connection is correctly configured
        :param e:
        :return:
        """
        self.tcResults.Clear()
        (db,proj) = self.__loadConnection()
        xnat = XnatConnector(self.configfile,db)
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


    def OnLaunch( self, event ):
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
            if len(scaninput)<=0 or len(scanoutput) <=0:
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
        #self.dirname = ''
        dlg = wx.DirDialog(self, "Choose a directory containing input files")
        if dlg.ShowModal() == wx.ID_OK:
            self.dirname = '"{0}"'.format(dlg.GetPath())
            self.dirname = dlg.GetPath()
            #self.StatusBar.SetStatusText("Loaded: %s\n" % self.dirname)
            self.inputedit.SetValue(self.dirname)
        dlg.Destroy()

    def OnEditDirname(self, event):
        self.dirname = '"{0}"'.format(event.GetString())
        self.dirname = event.GetString()
        #self.StatusBar.SetStatusText("Input dir: %s\n" % self.dirname)

    def OnDownload( self, event ):
        """
        Run downloads
        :param event:
        :return:
        """
        if self.dirname is None or len(self.dirname) <=0:
            dlg = wx.MessageDialog(self, "Please specify output directory", "OPEX Report", wx.OK)
            dlg.ShowModal()  # Show it
        else:
            msg = "Output directory for downloads: %s" % self.dirname
            dlg = wx.MessageDialog(self,msg , "OPEX Report", wx.OK)
            if dlg.ShowModal() == wx.ID_OK:
                runoption =['--output', self.dirname]
                (db, proj) = self.__loadConnection()

                xnat = XnatConnector(self.configfile, db)
                xnat.connect()
                subjects = xnat.getSubjectsDataframe(proj)
                op = OPEXReport(subjects=subjects,
                                opexfile=join(getcwd(),'resources', 'opex.csv'))
                op.xnat = xnat
                if op.downloadOPEXExpts(proj,self.dirname):
                    msg = "***Downloads Completed***"
                    logging.info(msg)
                else:
                    msg = "Error during download"
                    logging.error(msg)

                self.tcResults.AppendText(msg)

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



    def OnSelectData(self,event):
        """
        On data selection, enable Run
        :param event:
        :return:
        """
        if self.chOptions.GetStringSelection() != 'Select data':
            self.btnRun.Enable(True)
        else:
            self.btnRun.Enable(False)

    def OnSubmit(self,event):
        """
        Run OPEX Uploader
        :param event:
        :return:
        """
        self.tcResults.Clear()
        runoption = self.runoptions.get(self.chOptions.GetValue())[2:]

        (db, proj) = self.__loadConnection()
        if self.dirname is None or len(self.dirname) <=0:
            dlg = wx.MessageDialog(self, "Data directory not specified", "OPEX Uploader", wx.OK)
            dlg.ShowModal()  # Show it
            dlg.Destroy()
        else:
            #Load uploader args
            args = argparse.ArgumentParser(prog='OPEX Uploader')
            args.config=join(expanduser('~'), '.xnat.cfg')
            args.database = db
            args.projectcode = proj
            args.create = self.cbCreateSubject.GetValue()
            args.skiprows =self.cbSkiprows.GetValue()
            args.checks = self.cbChecks.GetValue()
            args.update = self.cbUpdate.GetValue()

            uploader = OPEXUploader(args)
            uploader.config()
            uploader.xnatconnect()
            msg = 'Connecting to Server:%s Project:%s' % (uploader.args.database, uploader.args.projectcode)
            logging.info(msg)
            print msg

            try:
                if uploader.xnat.testconnection():
                    logging.info("...Connected")
                    print "...Connected"
                    uploader.runDataUpload(proj, self.dirname, runoption)
                else:
                    raise ConnectionError('Not connected')


            except IOError as e:
                logging.error(e)
                print "Failed IO:", e
            except ConnectionError as e:
                logging.error(e)
                print "Failed connection:", e
            except ValueError as e:
                logging.error(e)
                print "ValueError:", e
            except Exception as e:
                logging.error(e)
                print "ERROR:", e
            finally:  # Processing complete
                uploader.xnatdisconnect()
                logging.info("FINISHED")
                print("FINISHED - see xnatupload.log for details")



def main():
    app = wx.App(False)
    OPEXUploaderGUI(None)
    app.MainLoop()

#Execute the application
if __name__ == '__main__':
    main()
