import logging
import sys
from datetime import datetime
from os import environ, access, R_OK, getcwd
from os.path import expanduser, join

import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
from configobj import ConfigObj

from xnatconnect.XnatConnector import XnatConnector  # Only for testing
from report.report import OPEXReport

""" 
OPEX Report DASHBOARD via DASH
https://plot.ly/python/create-online-dashboard/
"""

class OPEXReportApp(object):

    def __init__(self):
        self.app = dash.Dash(__name__)
        self.database = None
        self.project = None
        self.cache = None
        self.dbconfig = None
        self.df_participants = {}
        self.df_report = {}
        self.df_expts = {}
        self.__loadParams()
        logging.basicConfig(filename=self.logs, level=logging.DEBUG,
                            format='%(asctime)s %(message)s', datefmt='%d-%m-%Y %I:%M:%S %p')

    def __loadParams(self):
        home = expanduser('~')
        params = join(home,'.opex.cfg')
        if params is not None and access(params, R_OK):
            config = ConfigObj(params)
            self.database = config['DATABASE']
            self.project = config['PROJECT']
            self.cache = config['CACHEDIR']
            self.resources = config['RESOURCES']
            self.dbconfig = config['DBCONFIG']
            self.logs = config['LOGS']
        else:
            logging.error('Unable to read config - using defaults')
            self.database = 'xnat-dev-opex'
            self.project = 'P1'
            self.cache = 'cache'
            self.resources = 'resources'
            self.dbconfig = join(home,'.xnat.cfg')
            self.logs = join(home,'logs','xnatreport.log')

    def loadData(self):
        output = "RefreshCounts_%s.csv" % datetime.today().strftime("%Y%m%d")
        # output = "ExptCounts.csv"
        # outputfile = join(self.cache, output)


        # if exists(outputfile):
        #     report = OPEXReport(csvfile=outputfile)
        #     logging.info("Loading via cache")
        # else:
        #     logging.info("Loading from database")
        configfile = self.dbconfig
        xnat = XnatConnector(configfile, self.database)
        try:
            xnat.connect()
            if xnat.testconnection():
                print( "...Connected")
                output = "ExptCounts.csv"
                # outputfile = join(self.cache, output)
                # if access(outputfile, R_OK):
                #     csv = outputfile
                # else:
                #     csv = None
                subjects = xnat.getSubjectsDataframe(self.project)
                msg = "Loaded %d subjects from %s : %s" % (len(subjects), self.database, self.project)
                logging.info(msg)
                report = OPEXReport(subjects=subjects)
                report.xnat = xnat
                # Generate dataframes for display
                self.df_participants = report.getParticipants()
                logging.info('Participants loaded')
                #print self.df_participants
                self.df_report = report.printMissingExpts(self.project)
                self.df_report.sort_values(by=['MONTH', 'Subject'], inplace=True, ascending=False)
                logging.info("Missing experiments loaded")
                #print self.df_report.head()
                # Get expts
                self.df_expts = report.getExptCollection(projectcode=self.project)
                logging.info("Experiment collection loaded")
                #print self.df_expts.head()

        except IOError:
            logging.error("Connection error - terminating app")
            print( "Connection error - terminating app")
            sys.exit(1)
        finally:
            xnat.conn.disconnect()



    def colors(self):
        colors = {
        'background': '#111111',
        'text': '#7FDBFF'
        }
        return colors

    def tablecell(self,val, col):
        mycolors = list(['#F0F8FF','#E6E6FA','#B0E0E6','#ADD8E6','#87CEFA','#1E90FF','#6495ED','#4682B4','#5F9EA0','#4169E1','#00008B'])

        if type(val) != str:
            val = int(val)
            if val <= 0 and col != 'MONTH':
                return html.Td([html.Span(className="glyphicon glyphicon-ok")],
                               className="btn-success")
            # elif col =='Subject':
            #     return html.Td([html.A(val,href='https://opex.qbi.uq.edu.au:8443/app/action/QuickSearchAction#LINKxnat:subjectData_P1' )])
            else:
                valcolor = val % len(mycolors)
                return html.Td([html.Span(val)], style={'color':'black','background-color': mycolors[valcolor]})
        else:
            return html.Td(val)

    def generate_table(self,dataframe, max_rows=10):
        colors = self.colors()
        return html.Table(
            # Header
            [html.Tr([html.Th(col) for col in dataframe.columns])] +

            # Body
            [html.Tr([
                self.tablecell(dataframe.iloc[i][col], col) for col in dataframe.columns
            ]) for i in range(min(len(dataframe), max_rows))]
            ,
            className='table',
            style={
                    'textAlign': 'center',
                    'color': colors['text']
                })

    def participants_layout(self):
        logging.info("Loading data from db")
        self.loadData()
        logging.info("Data loaded - rendering")
        df = self.df_participants
        df_expts = self.df_expts
        df_report = self.df_report
        if df is None or df_expts is None or df_report is None:
            logging.error("No data to load")
            return 0

        colors = self.colors()
        title = 'OPEX XNAT participants [Total=' + str(sum(df['All'])) + ']'
        #self.app.css.append_css({"external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"})
        self.app.css.append_css({"external_url": "https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css"})
        return html.Div(className='container',
                                   style={'backgroundColor': colors['background']},
                                   children=[
        html.H1(children='OPEX Report',
                style={
                    'textAlign': 'center',
                    'color': colors['text']
                }
                ),

        html.Div(children=title,
                 style={
            'textAlign': 'center',
            'color': colors['text']
        }),

        dcc.Graph(
            id='participants',
            style={'width': '50%', 'float':'left'},
            figure={
                'data': [
                    {'x': df['Group'], 'y': df['Male'], 'type': 'bar', 'name': 'Male'},
                    {'x': df['Group'], 'y': df['Female'], 'type': 'bar', 'name': 'Female'},
                ],
                'layout': {
                    'barmode':'stack',
                    'plot_bgcolor': colors['background'],
                    'paper_bgcolor': colors['background'],
                    'title' : 'Participants',
                    'font': {
                        'color': colors['text']
                    }
                }
            }
        ),
        # Expts stacked bar
        dcc.Graph(
           id='expts',
           style={'width':'50%', 'float':'left'},
           figure=go.Figure(
               data=[
                   go.Pie(
                       values=df_expts.sum(),
                       labels=df_expts.columns,
                   )

               ],
               layout=go.Layout(
                       title='Experiments',
                       yaxis={'title': 'Expts Total'},
                       margin={'l': 40, 'b': 10, 't': 30, 'r': 10},
                       #legend={'x': 0, 'y': 1},
                       hovermode='closest',
                       font={ 'color': colors['text']},
                       plot_bgcolor= colors['background'],
                       paper_bgcolor= colors['background']
               )

           ),

        ),
        html.Div(id='missing',
                 children=[
           html.H3(children='Missing Data report',
                   style={
                       'textAlign': 'center',
                       'color': colors['text']
                   }),
            self.generate_table(df_report, max_rows=100)
            ])
    ])




#####################################################################

#for wsgi deployment
op = OPEXReportApp()
server  = op.app.server
server.secret_key = environ.get('SECRET_KEY', 'my-secret-key')
#op.loadData()
op.app.layout = op.participants_layout()


# for local deployment
if __name__ == '__main__':
    # op = OPEXReportApp()
    # op.loadData()
    # op.app.layout = op.participants_layout()
    op.app.run_server(debug=True, port=8089)
