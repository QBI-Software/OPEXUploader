# -*- coding: utf-8 -*- 

###########################################################################
## Python code generated with wxFormBuilder (version Jun 17 2015)
## http://www.wxformbuilder.org/
##
## PLEASE DO "NOT" EDIT THIS FILE!
###########################################################################

import wx
import wx.xrc

###########################################################################
## Class UploaderGUI
###########################################################################

class UploaderGUI ( wx.Frame ):
	
	def __init__( self, parent ):
		wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = u"XNAT Uploader", pos = wx.DefaultPosition, size = wx.Size( 783,860 ), style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL )
		
		self.SetSizeHintsSz( wx.DefaultSize, wx.DefaultSize )
		self.SetBackgroundColour( wx.Colour( 244, 254, 255 ) )
		
		bSizer1 = wx.BoxSizer( wx.VERTICAL )
		
		self.m_staticText1 = wx.StaticText( self, wx.ID_ANY, u"Upload Data to XNAT", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText1.Wrap( -1 )
		self.m_staticText1.SetFont( wx.Font( 12, 71, 90, 92, False, wx.EmptyString ) )
		
		bSizer1.Add( self.m_staticText1, 0, wx.ALL, 5 )
		
		self.m_staticline1 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		bSizer1.Add( self.m_staticline1, 0, wx.EXPAND |wx.ALL, 5 )
		
		fgSizer2 = wx.FlexGridSizer( 0, 2, 0, 0 )
		fgSizer2.SetFlexibleDirection( wx.BOTH )
		fgSizer2.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )
		
		self.m_staticText2 = wx.StaticText( self, wx.ID_ANY, u"Database config", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText2.Wrap( -1 )
		fgSizer2.Add( self.m_staticText2, 0, wx.ALL, 5 )
		
		dbeditChoices = []
		self.dbedit = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, wx.Size( 200,-1 ), dbeditChoices, 0 )
		self.dbedit.SetSelection( 0 )
		fgSizer2.Add( self.dbedit, 0, wx.ALL, 5 )
		
		self.m_staticText3 = wx.StaticText( self, wx.ID_ANY, u"Project code", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText3.Wrap( -1 )
		fgSizer2.Add( self.m_staticText3, 0, wx.ALL, 5 )
		
		self.projectedit = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 200,-1 ), 0 )
		fgSizer2.Add( self.projectedit, 0, wx.ALL, 5 )
		
		self.m_staticText5 = wx.StaticText( self, wx.ID_ANY, u"Data Type", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText5.Wrap( -1 )
		fgSizer2.Add( self.m_staticText5, 0, wx.ALL, 5 )
		
		chOptionsChoices = []
		self.chOptions = wx.ComboBox( self, wx.ID_ANY, u"Select data", wx.DefaultPosition, wx.Size( 200,-1 ), chOptionsChoices, 0 )
		fgSizer2.Add( self.chOptions, 0, wx.ALL, 5 )
		
		self.m_staticText4 = wx.StaticText( self, wx.ID_ANY, u"Input/Output directory", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText4.Wrap( -1 )
		self.m_staticText4.SetToolTipString( u"Provide input directory containing data files for upload OR output directory for CSV downloads" )
		
		fgSizer2.Add( self.m_staticText4, 0, wx.ALL, 5 )
		
		bSizer2 = wx.BoxSizer( wx.HORIZONTAL )
		
		self.inputedit = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 300,-1 ), 0 )
		bSizer2.Add( self.inputedit, 0, wx.ALL, 5 )
		
		self.btnInputdir = wx.Button( self, wx.ID_ANY, u"Browse", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer2.Add( self.btnInputdir, 0, wx.ALL, 5 )
		
		
		fgSizer2.Add( bSizer2, 1, wx.EXPAND, 5 )
		
		self.m_staticText6 = wx.StaticText( self, wx.ID_ANY, u"Report Only (output directory reqd)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText6.Wrap( -1 )
		fgSizer2.Add( self.m_staticText6, 0, wx.ALL, 5 )
		
		self.btnDownload = wx.Button( self, wx.ID_ANY, u"Download CSVs", wx.DefaultPosition, wx.DefaultSize, 0 )
		fgSizer2.Add( self.btnDownload, 0, wx.ALL, 5 )
		
		self.m_staticline4 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		fgSizer2.Add( self.m_staticline4, 0, wx.EXPAND |wx.ALL, 5 )
		
		self.m_staticline5 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		fgSizer2.Add( self.m_staticline5, 0, wx.EXPAND |wx.ALL, 5 )
		
		self.m_staticText14 = wx.StaticText( self, wx.ID_ANY, u"Scans Organizer (popup)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText14.Wrap( -1 )
		fgSizer2.Add( self.m_staticText14, 0, wx.ALL, 5 )
		
		self.btnLaunchscans = wx.Button( self, wx.ID_ANY, u"Launch", wx.DefaultPosition, wx.DefaultSize, 0 )
		fgSizer2.Add( self.btnLaunchscans, 0, wx.ALL, 5 )
		
		self.m_staticline2 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		fgSizer2.Add( self.m_staticline2, 0, wx.EXPAND |wx.ALL, 5 )
		
		self.m_staticline3 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		fgSizer2.Add( self.m_staticline3, 0, wx.EXPAND |wx.ALL, 5 )
		
		self.cbChecks = wx.CheckBox( self, wx.ID_ANY, u"TEST RUN only", wx.DefaultPosition, wx.DefaultSize, 0 )
		fgSizer2.Add( self.cbChecks, 0, wx.ALL, 5 )
		
		self.cbCreateSubject = wx.CheckBox( self, wx.ID_ANY, u"Create Subjects from data", wx.DefaultPosition, wx.DefaultSize, 0 )
		fgSizer2.Add( self.cbCreateSubject, 0, wx.ALL, 5 )
		
		self.cbSkiprows = wx.CheckBox( self, wx.ID_ANY, u"Skip ABORTED or NOT_RUN (Cantab)", wx.DefaultPosition, wx.DefaultSize, 0 )
		fgSizer2.Add( self.cbSkiprows, 0, wx.ALL, 5 )
		
		self.cbUpdate = wx.CheckBox( self, wx.ID_ANY, u"Update existing data", wx.DefaultPosition, wx.DefaultSize, 0 )
		fgSizer2.Add( self.cbUpdate, 0, wx.ALL, 5 )
		
		
		bSizer1.Add( fgSizer2, 1, wx.EXPAND, 5 )
		
		bSizer3 = wx.BoxSizer( wx.VERTICAL )
		
		self.tcResults = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 400,300 ), wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_WORDWRAP|wx.SIMPLE_BORDER )
		bSizer3.Add( self.tcResults, 0, wx.ALL|wx.EXPAND, 5 )
		
		bSizer4 = wx.BoxSizer( wx.HORIZONTAL )
		
		self.btnRun = wx.Button( self, wx.ID_ANY, u"RUN", wx.DefaultPosition, wx.DefaultSize, 0|wx.SIMPLE_BORDER )
		self.btnRun.SetForegroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_BTNFACE ) )
		self.btnRun.SetBackgroundColour( wx.Colour( 0, 128, 64 ) )
		self.btnRun.Enable( False )
		
		bSizer4.Add( self.btnRun, 0, wx.ALL, 5 )
		
		self.btnTest = wx.Button( self, wx.ID_ANY, u"Test Connection", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer4.Add( self.btnTest, 0, wx.ALL, 5 )
		
		self.m_button7 = wx.Button( self, wx.ID_ANY, u"Help", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer4.Add( self.m_button7, 0, wx.ALL, 5 )
		
		self.btnAbout = wx.Button( self, wx.ID_ANY, u"About", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer4.Add( self.btnAbout, 0, wx.ALL, 5 )
		
		self.btnSettings = wx.Button( self, wx.ID_ANY, u"Settings", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer4.Add( self.btnSettings, 0, wx.ALL, 5 )
		
		self.btnCancel = wx.Button( self, wx.ID_ANY, u"Cancel", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer4.Add( self.btnCancel, 0, wx.ALL, 5 )
		
		
		bSizer3.Add( bSizer4, 1, wx.EXPAND, 5 )
		
		
		bSizer1.Add( bSizer3, 1, wx.EXPAND, 5 )
		
		
		self.SetSizer( bSizer1 )
		self.Layout()
		
		self.Centre( wx.BOTH )
		
		# Connect Events
		self.chOptions.Bind( wx.EVT_COMBOBOX, self.OnSelectData )
		self.inputedit.Bind( wx.EVT_TEXT_ENTER, self.OnEditDirname )
		self.btnInputdir.Bind( wx.EVT_BUTTON, self.OnOpen )
		self.btnDownload.Bind( wx.EVT_BUTTON, self.OnDownload )
		self.btnLaunchscans.Bind( wx.EVT_BUTTON, self.OnLaunch )
		self.btnRun.Bind( wx.EVT_BUTTON, self.OnSubmit )
		self.btnTest.Bind( wx.EVT_BUTTON, self.OnTest )
		self.m_button7.Bind( wx.EVT_BUTTON, self.OnHelp )
		self.btnAbout.Bind( wx.EVT_BUTTON, self.OnAbout )
		self.btnSettings.Bind( wx.EVT_BUTTON, self.OnSettings )
		self.btnCancel.Bind( wx.EVT_BUTTON, self.OnClose )
	
	def __del__( self ):
		pass
	
	
	# Virtual event handlers, overide them in your derived class
	def OnSelectData( self, event ):
		event.Skip()
	
	def OnEditDirname( self, event ):
		event.Skip()
	
	def OnOpen( self, event ):
		event.Skip()
	
	def OnDownload( self, event ):
		event.Skip()
	
	def OnLaunch( self, event ):
		event.Skip()
	
	def OnSubmit( self, event ):
		event.Skip()
	
	def OnTest( self, event ):
		event.Skip()
	
	def OnHelp( self, event ):
		event.Skip()
	
	def OnAbout( self, event ):
		event.Skip()
	
	def OnSettings( self, event ):
		event.Skip()
	
	def OnClose( self, event ):
		event.Skip()
	

###########################################################################
## Class dlgScans
###########################################################################

class dlgScans ( wx.Dialog ):
	
	def __init__( self, parent ):
		wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"Scans organizer", pos = wx.DefaultPosition, size = wx.Size( 624,339 ), style = wx.DEFAULT_DIALOG_STYLE )
		
		self.SetSizeHintsSz( wx.DefaultSize, wx.DefaultSize )
		
		bSizer5 = wx.BoxSizer( wx.VERTICAL )
		
		self.m_staticText13 = wx.StaticText( self, wx.ID_ANY, u"Organizes scans into the correct directory structure for XNAT uploads.  \n-  Input directory must contain *.IMA or *.DCM files.\n-  Ignore directory contains already uploaded scans (eg 'done')", wx.DefaultPosition, wx.Size( 600,60 ), 0|wx.SUNKEN_BORDER )
		self.m_staticText13.Wrap( -1 )
		self.m_staticText13.SetFont( wx.Font( wx.NORMAL_FONT.GetPointSize(), 70, 90, 92, False, wx.EmptyString ) )
		
		bSizer5.Add( self.m_staticText13, 0, wx.ALL, 5 )
		
		self.chkOPEX = wx.CheckBox( self, wx.ID_ANY, u"OPEX IDs : extract Subject ID as first 6 characters", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.chkOPEX.SetValue(True) 
		bSizer5.Add( self.chkOPEX, 0, wx.ALL, 5 )
		
		fgSizer2 = wx.FlexGridSizer( 0, 2, 0, 0 )
		fgSizer2.SetFlexibleDirection( wx.BOTH )
		fgSizer2.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )
		
		self.m_staticText10 = wx.StaticText( self, wx.ID_ANY, u"Input directory", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText10.Wrap( -1 )
		self.m_staticText10.SetToolTipString( u"Expects: SUBJECTID/Group/*.IMA (mixed series)" )
		
		fgSizer2.Add( self.m_staticText10, 0, wx.ALL, 5 )
		
		self.txtInputScans = wx.DirPickerCtrl( self, wx.ID_ANY, wx.EmptyString, u"Select a folder for input", wx.DefaultPosition, wx.Size( 430,-1 ), wx.DIRP_DEFAULT_STYLE|wx.DIRP_DIR_MUST_EXIST )
		fgSizer2.Add( self.txtInputScans, 0, wx.ALL, 5 )
		
		self.m_staticText11 = wx.StaticText( self, wx.ID_ANY, u"Output sorted scans", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText11.Wrap( -1 )
		self.m_staticText11.SetToolTipString( u"Outputs format: sortedscans/SUBJECTID/scans/series/*.IMA" )
		
		fgSizer2.Add( self.m_staticText11, 0, wx.ALL, 5 )
		
		self.txtOutputScans = wx.DirPickerCtrl( self, wx.ID_ANY, wx.EmptyString, u"Select a folder", wx.DefaultPosition, wx.Size( 430,-1 ), wx.DIRP_DEFAULT_STYLE|wx.DIRP_DIR_MUST_EXIST )
		fgSizer2.Add( self.txtOutputScans, 0, wx.ALL, 5 )
		
		self.m_staticText12 = wx.StaticText( self, wx.ID_ANY, u"Ignore directory (optional)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText12.Wrap( -1 )
		self.m_staticText12.SetToolTipString( u"Optional - ignore these files (already done)" )
		
		fgSizer2.Add( self.m_staticText12, 0, wx.ALL, 5 )
		
		self.txtIgnoreScans = wx.DirPickerCtrl( self, wx.ID_ANY, wx.EmptyString, u"Select a folder", wx.DefaultPosition, wx.Size( 430,-1 ), wx.DIRP_DEFAULT_STYLE )
		fgSizer2.Add( self.txtIgnoreScans, 0, wx.ALL, 5 )
		
		
		bSizer5.Add( fgSizer2, 1, wx.EXPAND, 5 )
		
		m_sdbSizer1 = wx.StdDialogButtonSizer()
		self.m_sdbSizer1OK = wx.Button( self, wx.ID_OK )
		m_sdbSizer1.AddButton( self.m_sdbSizer1OK )
		self.m_sdbSizer1Cancel = wx.Button( self, wx.ID_CANCEL )
		m_sdbSizer1.AddButton( self.m_sdbSizer1Cancel )
		m_sdbSizer1.Realize();
		
		bSizer5.Add( m_sdbSizer1, 1, wx.EXPAND, 5 )
		
		
		self.SetSizer( bSizer5 )
		self.Layout()
		
		self.Centre( wx.BOTH )
	
	def __del__( self ):
		pass
	

###########################################################################
## Class dlgConfig
###########################################################################

class dlgConfig ( wx.Dialog ):
	
	def __init__( self, parent ):
		wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"Configuration Settings", pos = wx.DefaultPosition, size = wx.Size( 500,400 ), style = wx.DEFAULT_DIALOG_STYLE )
		
		self.SetSizeHintsSz( wx.DefaultSize, wx.DefaultSize )
		
		bSizer6 = wx.BoxSizer( wx.VERTICAL )
		
		self.m_staticText12 = wx.StaticText( self, wx.ID_ANY, u"Database connection parameters", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText12.Wrap( -1 )
		self.m_staticText12.SetFont( wx.Font( 14, 71, 90, 90, False, wx.EmptyString ) )
		
		bSizer6.Add( self.m_staticText12, 0, wx.ALL, 5 )
		
		fgSizer3 = wx.FlexGridSizer( 6, 2, 0, 0 )
		fgSizer3.SetFlexibleDirection( wx.BOTH )
		fgSizer3.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )
		
		self.m_staticText13 = wx.StaticText( self, wx.ID_ANY, u"Database config", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText13.Wrap( -1 )
		self.m_staticText13.SetToolTipString( u"Reference is used as 'Database Config' in main GUI" )
		
		fgSizer3.Add( self.m_staticText13, 0, wx.ALL, 5 )
		
		chConfigChoices = []
		self.chConfig = wx.ComboBox( self, wx.ID_ANY, u"Enter config ref", wx.DefaultPosition, wx.DefaultSize, chConfigChoices, 0 )
		fgSizer3.Add( self.chConfig, 0, wx.ALL, 5 )
		
		self.m_staticText14 = wx.StaticText( self, wx.ID_ANY, u"URL", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText14.Wrap( -1 )
		fgSizer3.Add( self.m_staticText14, 0, wx.ALL, 5 )
		
		self.txtURL = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 300,-1 ), 0 )
		fgSizer3.Add( self.txtURL, 0, wx.ALL, 5 )
		
		self.m_staticText15 = wx.StaticText( self, wx.ID_ANY, u"Username", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText15.Wrap( -1 )
		fgSizer3.Add( self.m_staticText15, 0, wx.ALL, 5 )
		
		self.txtUser = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 200,-1 ), 0 )
		fgSizer3.Add( self.txtUser, 0, wx.ALL, 5 )
		
		self.m_staticText16 = wx.StaticText( self, wx.ID_ANY, u"Password", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText16.Wrap( -1 )
		fgSizer3.Add( self.m_staticText16, 0, wx.ALL, 5 )
		
		self.txtPass = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 200,-1 ), 0 )
		fgSizer3.Add( self.txtPass, 0, wx.ALL, 5 )
		
		
		bSizer6.Add( fgSizer3, 1, wx.EXPAND, 5 )
		
		self.m_staticline6 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		bSizer6.Add( self.m_staticline6, 0, wx.EXPAND |wx.ALL, 5 )
		
		bSizer8 = wx.BoxSizer( wx.HORIZONTAL )
		
		self.btnSaveConfig = wx.Button( self, wx.ID_ANY, u"Save", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.btnSaveConfig.SetDefault() 
		bSizer8.Add( self.btnSaveConfig, 0, wx.ALL, 5 )
		
		self.btnLoadConfig = wx.Button( self, wx.ID_ANY, u"Load", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer8.Add( self.btnLoadConfig, 0, wx.ALL, 5 )
		
		self.btnRemove = wx.Button( self, wx.ID_ANY, u"Remove", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer8.Add( self.btnRemove, 0, wx.ALL, 5 )
		
		
		bSizer6.Add( bSizer8, 1, wx.EXPAND, 5 )
		
		
		self.SetSizer( bSizer6 )
		self.Layout()
		
		self.Centre( wx.BOTH )
		
		# Connect Events
		self.chConfig.Bind( wx.EVT_COMBOBOX, self.OnConfigSelect )
		self.chConfig.Bind( wx.EVT_TEXT_ENTER, self.OnConfigText )
		self.btnSaveConfig.Bind( wx.EVT_BUTTON, self.OnSaveConfig )
		self.btnLoadConfig.Bind( wx.EVT_BUTTON, self.OnLoadConfig )
		self.btnRemove.Bind( wx.EVT_BUTTON, self.OnRemoveConfig )
	
	def __del__( self ):
		pass
	
	
	# Virtual event handlers, overide them in your derived class
	def OnConfigSelect( self, event ):
		event.Skip()
	
	def OnConfigText( self, event ):
		event.Skip()
	
	def OnSaveConfig( self, event ):
		event.Skip()
	
	def OnLoadConfig( self, event ):
		event.Skip()
	
	def OnRemoveConfig( self, event ):
		event.Skip()
	

