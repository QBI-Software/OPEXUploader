# -*- coding: utf-8 -*- 

###########################################################################
## Python code generated with wxFormBuilder (version Jun 17 2015)
## http://www.wxformbuilder.org/
##
## PLEASE DO "NOT" EDIT THIS FILE!
###########################################################################

import wx
import wx.xrc
import wx.grid
import wx.html

###########################################################################
## Class UploaderGUI
###########################################################################

class UploaderGUI ( wx.Frame ):
	
	def __init__( self, parent ):
		wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = u"XNAT Uploader", pos = wx.DefaultPosition, size = wx.Size( 936,860 ), style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL )
		
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
		
		self.m_staticText4 = wx.StaticText( self, wx.ID_ANY, u"Input data directory", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText4.Wrap( -1 )
		self.m_staticText4.SetToolTipString( u"Provide input directory containing data files for upload OR output directory for CSV downloads" )
		
		fgSizer2.Add( self.m_staticText4, 0, wx.ALL, 5 )
		
		bSizer2 = wx.BoxSizer( wx.HORIZONTAL )
		
		self.inputedit = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 300,-1 ), 0 )
		bSizer2.Add( self.inputedit, 0, wx.ALL, 5 )
		
		self.btnInputdir = wx.Button( self, wx.ID_ANY, u"Browse", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer2.Add( self.btnInputdir, 0, wx.ALL, 5 )
		
		
		fgSizer2.Add( bSizer2, 1, wx.EXPAND, 5 )
		
		self.m_staticline4 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		fgSizer2.Add( self.m_staticline4, 0, wx.EXPAND |wx.ALL, 5 )
		
		self.m_staticline5 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		fgSizer2.Add( self.m_staticline5, 0, wx.EXPAND |wx.ALL, 5 )
		
		self.cbCreateSubject = wx.CheckBox( self, wx.ID_ANY, u"Create Subjects from CANTAB data", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.cbCreateSubject.SetToolTipString( u"Use only if certain that all participant IDs are valid. Mostly this is not used." )
		
		fgSizer2.Add( self.cbCreateSubject, 0, wx.ALL, 5 )
		
		self.cbUpdate = wx.CheckBox( self, wx.ID_ANY, u"Update existing data for selected experiment type", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.cbUpdate.SetToolTipString( u"Will overwrite any existing data in XNAT" )
		
		fgSizer2.Add( self.cbUpdate, 0, wx.ALL, 5 )
		
		self.cbChecks = wx.CheckBox( self, wx.ID_ANY, u"TEST RUN only", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.cbChecks.SetToolTipString( u"This checks the data in the input file can be read properly by the script (not the database)." )
		
		fgSizer2.Add( self.cbChecks, 0, wx.ALL, 5 )
		
		
		bSizer1.Add( fgSizer2, 1, wx.EXPAND, 5 )
		
		bSizer4 = wx.BoxSizer( wx.HORIZONTAL )
		
		self.btnRun = wx.Button( self, wx.ID_ANY, u"RUN", wx.DefaultPosition, wx.DefaultSize, 0|wx.SIMPLE_BORDER )
		self.btnRun.SetForegroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_BTNFACE ) )
		self.btnRun.SetBackgroundColour( wx.Colour( 0, 128, 64 ) )
		self.btnRun.Enable( False )
		
		bSizer4.Add( self.btnRun, 0, wx.ALL, 5 )
		
		self.m_button13 = wx.Button( self, wx.ID_ANY, u"Test Connection", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer4.Add( self.m_button13, 0, wx.ALL, 5 )
		
		self.m_button15 = wx.Button( self, wx.ID_ANY, u"Clear Output", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer4.Add( self.m_button15, 0, wx.ALL, 5 )
		
		self.m_button17 = wx.Button( self, wx.ID_ANY, u"View Log", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer4.Add( self.m_button17, 0, wx.ALL, 5 )
		
		self.btnCancel = wx.Button( self, wx.ID_ANY, u"Exit", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer4.Add( self.btnCancel, 0, wx.ALL, 5 )
		
		
		bSizer1.Add( bSizer4, 1, wx.EXPAND, 5 )
		
		bSizer3 = wx.BoxSizer( wx.VERTICAL )
		
		self.tcResults = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.TE_MULTILINE|wx.TE_READONLY )
		self.tcResults.SetMinSize( wx.Size( 900,450 ) )
		
		bSizer3.Add( self.tcResults, 0, wx.ALL, 5 )
		
		
		bSizer1.Add( bSizer3, 1, wx.EXPAND, 5 )
		
		
		self.SetSizer( bSizer1 )
		self.Layout()
		self.m_menubar1 = wx.MenuBar( 0 )
		self.m_menu3 = wx.Menu()
		self.m_menuItem4 = wx.MenuItem( self.m_menu3, wx.ID_ANY, u"Database", wx.EmptyString, wx.ITEM_NORMAL )
		self.m_menu3.AppendItem( self.m_menuItem4 )
		
		self.m_menuItem5 = wx.MenuItem( self.m_menu3, wx.ID_ANY, u"Incorrect IDs", wx.EmptyString, wx.ITEM_NORMAL )
		self.m_menu3.AppendItem( self.m_menuItem5 )
		
		self.m_menubar1.Append( self.m_menu3, u"Settings" ) 
		
		self.m_menu1 = wx.Menu()
		self.m_menuItem1 = wx.MenuItem( self.m_menu1, wx.ID_ANY, u"MRI Scans Organizer", wx.EmptyString, wx.ITEM_NORMAL )
		self.m_menu1.AppendItem( self.m_menuItem1 )
		
		self.m_menuItem6 = wx.MenuItem( self.m_menu1, wx.ID_ANY, u"Download CSVs", wx.EmptyString, wx.ITEM_NORMAL )
		self.m_menu1.AppendItem( self.m_menuItem6 )
		
		self.m_menuItem61 = wx.MenuItem( self.m_menu1, wx.ID_ANY, u"Generate Reports", wx.EmptyString, wx.ITEM_NORMAL )
		self.m_menu1.AppendItem( self.m_menuItem61 )
		
		self.m_menuItem81 = wx.MenuItem( self.m_menu1, wx.ID_ANY, u"View Log", wx.EmptyString, wx.ITEM_NORMAL )
		self.m_menu1.AppendItem( self.m_menuItem81 )
		
		self.m_menubar1.Append( self.m_menu1, u"Tools" ) 
		
		self.m_menu2 = wx.Menu()
		self.m_menuItem2 = wx.MenuItem( self.m_menu2, wx.ID_ANY, u"Help", wx.EmptyString, wx.ITEM_NORMAL )
		self.m_menu2.AppendItem( self.m_menuItem2 )
		
		self.m_menuItem3 = wx.MenuItem( self.m_menu2, wx.ID_ANY, u"About", wx.EmptyString, wx.ITEM_NORMAL )
		self.m_menu2.AppendItem( self.m_menuItem3 )
		
		self.m_menubar1.Append( self.m_menu2, u"Help" ) 
		
		self.SetMenuBar( self.m_menubar1 )
		
		self.m_statusBar1 = self.CreateStatusBar( 1, 0, wx.ID_ANY )
		
		self.Centre( wx.BOTH )
		
		# Connect Events
		self.chOptions.Bind( wx.EVT_COMBOBOX, self.OnSelectData )
		self.inputedit.Bind( wx.EVT_TEXT_ENTER, self.OnEditDirname )
		self.btnInputdir.Bind( wx.EVT_BUTTON, self.OnOpen )
		self.btnRun.Bind( wx.EVT_BUTTON, self.OnSubmit )
		self.m_button13.Bind( wx.EVT_BUTTON, self.OnTest )
		self.m_button15.Bind( wx.EVT_BUTTON, self.OnClearOutput )
		self.m_button17.Bind( wx.EVT_BUTTON, self.OnLog )
		self.btnCancel.Bind( wx.EVT_BUTTON, self.OnExit )
		self.Bind( wx.EVT_MENU, self.OnSettings, id = self.m_menuItem4.GetId() )
		self.Bind( wx.EVT_MENU, self.OnIds, id = self.m_menuItem5.GetId() )
		self.Bind( wx.EVT_MENU, self.OnLaunch, id = self.m_menuItem1.GetId() )
		self.Bind( wx.EVT_MENU, self.OnDownload, id = self.m_menuItem6.GetId() )
		self.Bind( wx.EVT_MENU, self.OnReport, id = self.m_menuItem61.GetId() )
		self.Bind( wx.EVT_MENU, self.OnLog, id = self.m_menuItem81.GetId() )
		self.Bind( wx.EVT_MENU, self.OnHelp, id = self.m_menuItem2.GetId() )
		self.Bind( wx.EVT_MENU, self.OnAbout, id = self.m_menuItem3.GetId() )
	
	def __del__( self ):
		pass
	
	
	# Virtual event handlers, overide them in your derived class
	def OnSelectData( self, event ):
		event.Skip()
	
	def OnEditDirname( self, event ):
		event.Skip()
	
	def OnOpen( self, event ):
		event.Skip()
	
	def OnSubmit( self, event ):
		event.Skip()
	
	def OnTest( self, event ):
		event.Skip()
	
	def OnClearOutput( self, event ):
		event.Skip()
	
	def OnLog( self, event ):
		event.Skip()
	
	def OnExit( self, event ):
		event.Skip()
	
	def OnSettings( self, event ):
		event.Skip()
	
	def OnIds( self, event ):
		event.Skip()
	
	def OnLaunch( self, event ):
		event.Skip()
	
	def OnDownload( self, event ):
		event.Skip()
	
	def OnReport( self, event ):
		event.Skip()
	
	
	def OnHelp( self, event ):
		event.Skip()
	
	def OnAbout( self, event ):
		event.Skip()
	

###########################################################################
## Class dlgDownloads
###########################################################################

class dlgDownloads ( wx.Dialog ):
	
	def __init__( self, parent ):
		wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"Download CSVs", pos = wx.DefaultPosition, size = wx.Size( 502,470 ), style = wx.CLOSE_BOX|wx.DEFAULT_DIALOG_STYLE )
		
		self.SetSizeHintsSz( wx.DefaultSize, wx.DefaultSize )
		
		bSizer12 = wx.BoxSizer( wx.VERTICAL )
		
		self.m_staticText26 = wx.StaticText( self, wx.ID_ANY, u"Download Experiment data as CSV files", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText26.Wrap( -1 )
		bSizer12.Add( self.m_staticText26, 0, wx.ALL, 5 )
		
		self.chDelta = wx.CheckBox( self, wx.ID_ANY, u"Include Deltas", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer12.Add( self.chDelta, 0, wx.ALL, 5 )
		
		bSizer13 = wx.BoxSizer( wx.HORIZONTAL )
		
		self.m_staticText27 = wx.StaticText( self, wx.ID_ANY, u"Select directory", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText27.Wrap( -1 )
		bSizer13.Add( self.m_staticText27, 0, wx.ALL, 5 )
		
		self.m_downloaddir = wx.GenericDirCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( -1,300 ), wx.DIRCTRL_3D_INTERNAL|wx.DIRCTRL_DIR_ONLY|wx.SUNKEN_BORDER, wx.EmptyString, 0 )
		
		self.m_downloaddir.ShowHidden( False )
		bSizer13.Add( self.m_downloaddir, 1, wx.EXPAND |wx.ALL, 5 )
		
		
		bSizer12.Add( bSizer13, 1, wx.EXPAND, 5 )
		
		bSizer15 = wx.BoxSizer( wx.HORIZONTAL )
		
		self.m_button17 = wx.Button( self, wx.ID_ANY, u"Download", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_button17.SetFont( wx.Font( wx.NORMAL_FONT.GetPointSize(), 71, 90, 90, False, wx.EmptyString ) )
		self.m_button17.SetForegroundColour( wx.Colour( 255, 255, 0 ) )
		self.m_button17.SetBackgroundColour( wx.Colour( 0, 128, 64 ) )
		
		bSizer15.Add( self.m_button17, 0, wx.ALL, 5 )
		
		self.m_button18 = wx.Button( self, wx.ID_ANY, u"Cancel", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer15.Add( self.m_button18, 0, wx.ALL, 5 )
		
		
		bSizer12.Add( bSizer15, 1, wx.EXPAND, 5 )
		
		
		self.SetSizer( bSizer12 )
		self.Layout()
		
		self.Centre( wx.BOTH )
		
		# Connect Events
		self.Bind( wx.EVT_INIT_DIALOG, self.OnDownload )
		self.m_button17.Bind( wx.EVT_BUTTON, self.OnCSVDownload )
		self.m_button18.Bind( wx.EVT_BUTTON, self.OnCloseDlg )
	
	def __del__( self ):
		pass
	
	
	# Virtual event handlers, overide them in your derived class
	def OnDownload( self, event ):
		event.Skip()
	
	def OnCSVDownload( self, event ):
		event.Skip()
	
	def OnCloseDlg( self, event ):
		event.Skip()
	

###########################################################################
## Class dlgReports
###########################################################################

class dlgReports ( wx.Dialog ):
	
	def __init__( self, parent ):
		wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"Reports", pos = wx.DefaultPosition, size = wx.Size( 502,470 ), style = wx.CLOSE_BOX|wx.DEFAULT_DIALOG_STYLE )
		
		self.SetSizeHintsSz( wx.DefaultSize, wx.DefaultSize )
		
		bSizer12 = wx.BoxSizer( wx.VERTICAL )
		
		self.m_staticText26 = wx.StaticText( self, wx.ID_ANY, u"Generate Reports from Experiment Data (may include html plots which may launch in a browser)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText26.Wrap( 400 )
		self.m_staticText26.SetFont( wx.Font( wx.NORMAL_FONT.GetPointSize(), 70, 90, 92, False, wx.EmptyString ) )
		
		bSizer12.Add( self.m_staticText26, 0, wx.ALL, 5 )
		
		self.chDelta = wx.CheckBox( self, wx.ID_ANY, u"Include Deltas", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer12.Add( self.chDelta, 0, wx.ALL, 5 )
		
		bSizer13 = wx.BoxSizer( wx.HORIZONTAL )
		
		self.m_staticText27 = wx.StaticText( self, wx.ID_ANY, u"Select directory", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText27.Wrap( -1 )
		bSizer13.Add( self.m_staticText27, 0, wx.ALL, 5 )
		
		self.m_downloaddir = wx.GenericDirCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( -1,300 ), wx.DIRCTRL_3D_INTERNAL|wx.DIRCTRL_DIR_ONLY|wx.SUNKEN_BORDER, wx.EmptyString, 0 )
		
		self.m_downloaddir.ShowHidden( False )
		bSizer13.Add( self.m_downloaddir, 1, wx.EXPAND |wx.ALL, 5 )
		
		
		bSizer12.Add( bSizer13, 1, wx.EXPAND, 5 )
		
		bSizer15 = wx.BoxSizer( wx.HORIZONTAL )
		
		self.m_button17 = wx.Button( self, wx.ID_ANY, u"Generate", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_button17.SetFont( wx.Font( wx.NORMAL_FONT.GetPointSize(), 70, 90, 90, False, wx.EmptyString ) )
		self.m_button17.SetForegroundColour( wx.Colour( 255, 255, 0 ) )
		self.m_button17.SetBackgroundColour( wx.Colour( 0, 128, 64 ) )
		
		bSizer15.Add( self.m_button17, 0, wx.ALL, 5 )
		
		self.m_button18 = wx.Button( self, wx.ID_ANY, u"Cancel", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer15.Add( self.m_button18, 0, wx.ALL, 5 )
		
		
		bSizer12.Add( bSizer15, 1, wx.EXPAND, 5 )
		
		
		self.SetSizer( bSizer12 )
		self.Layout()
		
		self.Centre( wx.BOTH )
		
		# Connect Events
		self.Bind( wx.EVT_INIT_DIALOG, self.OnDownload )
		self.m_button17.Bind( wx.EVT_BUTTON, self.OnGenerateReports )
		self.m_button18.Bind( wx.EVT_BUTTON, self.OnCloseDlg )
	
	def __del__( self ):
		pass
	
	
	# Virtual event handlers, overide them in your derived class
	def OnDownload( self, event ):
		event.Skip()
	
	def OnGenerateReports( self, event ):
		event.Skip()
	
	def OnCloseDlg( self, event ):
		event.Skip()
	

###########################################################################
## Class dlgIDS
###########################################################################

class dlgIDS ( wx.Dialog ):
	
	def __init__( self, parent ):
		wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"Incorrect IDs", pos = wx.DefaultPosition, size = wx.Size( -1,-1 ), style = wx.DEFAULT_DIALOG_STYLE )
		
		self.SetSizeHintsSz( wx.Size( 200,300 ), wx.DefaultSize )
		
		bSizer10 = wx.BoxSizer( wx.VERTICAL )
		
		self.m_staticText20 = wx.StaticText( self, wx.ID_ANY, u"Enter Incorrect IDs to replace in data uploads.  Press Enter key after entering text then click \"Save\". To remove, clear entries then \"Save\".", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText20.Wrap( 500 )
		bSizer10.Add( self.m_staticText20, 0, wx.ALL, 5 )
		
		self.m_grid1 = wx.grid.Grid( self, wx.ID_ANY, wx.DefaultPosition, wx.Size( -1,-1 ), 0 )
		
		# Grid
		self.m_grid1.CreateGrid( 15, 2 )
		self.m_grid1.EnableEditing( True )
		self.m_grid1.EnableGridLines( True )
		self.m_grid1.EnableDragGridSize( True )
		self.m_grid1.SetMargins( 0, 0 )
		
		# Columns
		self.m_grid1.SetColSize( 0, 200 )
		self.m_grid1.SetColSize( 1, 200 )
		self.m_grid1.EnableDragColMove( False )
		self.m_grid1.EnableDragColSize( True )
		self.m_grid1.SetColLabelSize( 60 )
		self.m_grid1.SetColLabelValue( 0, u"INCORRECT" )
		self.m_grid1.SetColLabelValue( 1, u"CORRECT" )
		self.m_grid1.SetColLabelAlignment( wx.ALIGN_CENTRE, wx.ALIGN_CENTRE )
		
		# Rows
		self.m_grid1.AutoSizeRows()
		self.m_grid1.EnableDragRowSize( True )
		self.m_grid1.SetRowLabelSize( 100 )
		self.m_grid1.SetRowLabelAlignment( wx.ALIGN_CENTRE, wx.ALIGN_CENTRE )
		
		# Label Appearance
		
		# Cell Defaults
		self.m_grid1.SetDefaultCellAlignment( wx.ALIGN_LEFT, wx.ALIGN_TOP )
		self.m_grid1.SetMinSize( wx.Size( 500,500 ) )
		
		bSizer10.Add( self.m_grid1, 0, wx.ALL, 5 )
		
		bSizer11 = wx.BoxSizer( wx.HORIZONTAL )
		
		self.btnSaveIds = wx.Button( self, wx.ID_ANY, u"Save", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.btnSaveIds.SetForegroundColour( wx.Colour( 255, 255, 0 ) )
		self.btnSaveIds.SetBackgroundColour( wx.Colour( 0, 128, 64 ) )
		
		bSizer11.Add( self.btnSaveIds, 0, wx.ALL, 5 )
		
		self.btnCancelIds = wx.Button( self, wx.ID_ANY, u"Cancel", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer11.Add( self.btnCancelIds, 0, wx.ALL, 5 )
		
		self.btnAddID = wx.Button( self, wx.ID_ANY, u"Add", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer11.Add( self.btnAddID, 0, wx.ALL, 5 )
		
		
		bSizer10.Add( bSizer11, 1, wx.EXPAND, 5 )
		
		
		self.SetSizer( bSizer10 )
		self.Layout()
		bSizer10.Fit( self )
		
		self.Centre( wx.BOTH )
		
		# Connect Events
		self.m_grid1.Bind( wx.grid.EVT_GRID_CELL_RIGHT_CLICK, self.OnDeleteRow )
		self.btnSaveIds.Bind( wx.EVT_BUTTON, self.OnSaveIds )
		self.btnCancelIds.Bind( wx.EVT_BUTTON, self.OnCloseDlg )
		self.btnAddID.Bind( wx.EVT_BUTTON, self.OnAddRow )
	
	def __del__( self ):
		pass
	
	
	# Virtual event handlers, overide them in your derived class
	def OnDeleteRow( self, event ):
		event.Skip()
	
	def OnSaveIds( self, event ):
		event.Skip()
	
	def OnCloseDlg( self, event ):
		event.Skip()
	
	def OnAddRow( self, event ):
		event.Skip()
	

###########################################################################
## Class dlgScans
###########################################################################

class dlgScans ( wx.Dialog ):
	
	def __init__( self, parent ):
		wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"Scans organizer", pos = wx.DefaultPosition, size = wx.Size( 830,670 ), style = wx.DEFAULT_DIALOG_STYLE )
		
		self.SetSizeHintsSz( wx.DefaultSize, wx.DefaultSize )
		
		bSizer5 = wx.BoxSizer( wx.VERTICAL )
		
		self.m_staticText13 = wx.StaticText( self, wx.ID_ANY, u"Step 1 Organizes scans into the correct directory structure for XNAT uploads (Step 2).  \n-  Input directory is top level with subdirectories named as subject ID containing raw *.IMA or *.DCM files.\n- Output Sorted Scans will be used for Step 2 upload (create this if it doesn't exist)\n-  Ignore directory contains already uploaded scans (eg 'done'). Note when upload is complete, move sorted scans here manually for next time or create empty folders with same names.\n\nStep 2 is run from main application - select MRI and this output directory as the input directory.", wx.DefaultPosition, wx.Size( 700,200 ), 0|wx.SUNKEN_BORDER )
		self.m_staticText13.Wrap( -1 )
		self.m_staticText13.SetFont( wx.Font( wx.NORMAL_FONT.GetPointSize(), 70, 90, 92, False, wx.EmptyString ) )
		
		bSizer5.Add( self.m_staticText13, 0, wx.ALL, 5 )
		
		self.chkOPEX = wx.CheckBox( self, wx.ID_ANY, u"Extract Subject ID as prefix (eg 1001DD01 to 1001DD)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.chkOPEX.SetValue(True) 
		bSizer5.Add( self.chkOPEX, 0, wx.ALL, 5 )
		
		fgSizer2 = wx.FlexGridSizer( 0, 2, 0, 0 )
		fgSizer2.SetFlexibleDirection( wx.BOTH )
		fgSizer2.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )
		
		self.m_staticText21 = wx.StaticText( self, wx.ID_ANY, u"Number of characters in prefix (subject ID)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText21.Wrap( -1 )
		fgSizer2.Add( self.m_staticText21, 0, wx.ALL, 5 )
		
		self.m_spinCtrlChars = wx.SpinCtrl( self, wx.ID_ANY, u"6", wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 20, 0 )
		fgSizer2.Add( self.m_spinCtrlChars, 0, wx.ALL, 5 )
		
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
		
		self.txtIgnoreScans = wx.DirPickerCtrl( self, wx.ID_ANY, wx.EmptyString, u"Select a folder", wx.DefaultPosition, wx.Size( 430,-1 ), wx.DIRP_DEFAULT_STYLE|wx.DIRP_DIR_MUST_EXIST )
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
## Class dlgHelp
###########################################################################

class dlgHelp ( wx.Dialog ):
	
	def __init__( self, parent ):
		wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"Help", pos = wx.DefaultPosition, size = wx.Size( 694,479 ), style = wx.DEFAULT_DIALOG_STYLE )
		
		self.SetSizeHintsSz( wx.DefaultSize, wx.DefaultSize )
		
		bSizer5 = wx.BoxSizer( wx.VERTICAL )
		
		self.m_staticText25 = wx.StaticText( self, wx.ID_ANY, u"Quick User Guide", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText25.Wrap( -1 )
		self.m_staticText25.SetFont( wx.Font( 14, 71, 90, 92, False, wx.EmptyString ) )
		
		bSizer5.Add( self.m_staticText25, 0, wx.ALL, 5 )
		
		self.m_htmlWin1 = wx.html.HtmlWindow( self, wx.ID_ANY, wx.DefaultPosition, wx.Size( 700,350 ), wx.html.HW_SCROLLBAR_AUTO )
		bSizer5.Add( self.m_htmlWin1, 0, wx.ALL|wx.EXPAND, 5 )
		
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
		wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"Configuration Settings", pos = wx.DefaultPosition, size = wx.Size( 499,320 ), style = wx.DEFAULT_DIALOG_STYLE )
		
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
	

###########################################################################
## Class dlgLogViewer
###########################################################################

class dlgLogViewer ( wx.Dialog ):
	
	def __init__( self, parent ):
		wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"Upload Log Output", pos = wx.DefaultPosition, size = wx.DefaultSize, style = wx.DEFAULT_DIALOG_STYLE )
		
		self.SetSizeHintsSz( wx.Size( 600,600 ), wx.DefaultSize )
		
		bSizer17 = wx.BoxSizer( wx.VERTICAL )
		
		self.tcLog = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_WORDWRAP )
		self.tcLog.SetMinSize( wx.Size( 580,500 ) )
		
		bSizer17.Add( self.tcLog, 0, wx.ALL, 5 )
		
		self.m_button16 = wx.Button( self, wx.ID_ANY, u"Refresh", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer17.Add( self.m_button16, 0, wx.ALL, 5 )
		
		
		self.SetSizer( bSizer17 )
		self.Layout()
		bSizer17.Fit( self )
		
		self.Centre( wx.BOTH )
		
		# Connect Events
		self.m_button16.Bind( wx.EVT_BUTTON, self.OnRefresh )
	
	def __del__( self ):
		pass
	
	
	# Virtual event handlers, overide them in your derived class
	def OnRefresh( self, event ):
		event.Skip()
	

