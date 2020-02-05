"""
Title:  Amunet Filter
Author: Alan Ho
Date Created:   24/01/2019
Description: Contains the functions for filtering amunet all data and can be applied to either a complete data.frame or
partial data.frames within amunetParser loop. Also contains amunetAnalysis module which can be used to run simple ANOVAs on
the delta change
"""
import argparse
from datetime import datetime
from functools import reduce
from itertools import product
from os.path import join

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.api as sm
from statsmodels.formula.api import ols

# PARAMETERS ----------------------------------------------------------
amunetindex = ['Subject', 'Type', 'Visit', 'interval', 'date', 'experiments', 'trials']
key_experiments = ['Allo Virtual', 'AlloEgo Virtual', 'Ego Virtual']
key_fields = ['TotalError', 'Duration', 'PathLength']

# CLASS / FUNCTION DEFINITIONS ----------------------------------------

class amunetFilter:

    def __init__(self, df, errorfile=None, index=['Subject', 'Type', 'Visit', 'interval', 'date', 'experiments', 'trials']):
        self.df = df
        self.errorfile = errorfile
        self.index = index
        if errorfile is not None:
            self.errors = pd.read_csv(errorfile)

    def BYerrors(self):
        self.df = self.df[~(self.df == 0).all(axis=1)]. \
                    query("PathLength > 0 & TotalError > 0")
        return self

    def BYclinicanerrors(self):
        self.errors['marker'] = 1
        joined = pd.merge(self.df.reset_index(), self.errors, how='left')
        self.df = joined[pd.isnull(joined['marker'])][self.df.reset_index().columns].\
                    set_index(self.index)
        return self

    def BYtrial(self, omit=None, ignoretype="Amunet 2", experiments=['Allo Virtual', 'AlloEgo Virtual', 'Ego Virtual']):
        # omits particular trials by experiment type (currently only supoorted for amunet 1)
        querystatement = 'Type == "{}" | (experiments in {} & trials not in {})'.format(ignoretype,experiments,omit)
        self.df = self.df.query(querystatement)
        return self


class amunetAnalysis:

    def __init__(self, inputdir, filename, errorfile):

        self.inputdir = inputdir
        self.errorfile = errorfile
        self.filename = filename
        self.palette = {'AIT':"#E92323", 'MIT' : "#0037F6", 'LIT': "#58F520" }

        self.getData()
        self.getFiltered()
        self.sumInterval()
        self.getDelta()

    def getData(self):
        self.data = pd.read_csv(join(self.inputdir, self.filename)).\
                        set_index(amunetindex)

    def getFiltered(self):
        results = {}
        for i in range(0, 5):
            self.filter = applyFilter(self.data, self.errorfile, filter_type=i)

            num_trials = self.filter. \
                reset_index(). \
                set_index(['Subject', 'experiments', 'interval']). \
                filter(items=['trials']). \
                pivot_table(index=['experiments', 'interval'],
                            values='trials',
                            aggfunc=lambda x: len(x.unique()))

            num_subjects = self.filter. \
                reset_index(). \
                set_index(['experiments', 'interval']). \
                filter(items=['Subject']). \
                pivot_table(index=['experiments', 'interval'],
                            values='Subject',
                            aggfunc=lambda x: len(x.unique()))

            sum_results = self.filter. \
                query('experiments in {}'.format(key_experiments)). \
                pivot_table(index=['Subject', 'interval', 'experiments'],
                            values=['Duration', 'TotalError', 'PathLength'],
                            aggfunc={'Duration': np.sum, 'TotalError': np.mean, 'PathLength': np.mean}). \
                stack(). \
                reset_index(). \
                rename(columns={0: 'Filter_' + str(i), 'level_3': 'variable'})

            results[i] = {
                'num_trials': num_trials,
                'num_subjects': num_subjects,
                'sum_results': sum_results
            }

        listofresults = [results[i]['sum_results'] for i in range(0, 5)]
        self.filterdata = pd.read_csv('C:\\Users\\uqaho4\Desktop\hMWM\P1_subjectlist.csv'). \
            rename(columns={'ID': 'Subject', 'group': 'Exercise'}). \
            filter(items=['Subject', 'Exercise']). \
            query('Exercise in ("AIT", "MIT", "LIT")'). \
            merge(reduce(lambda x, y: pd.merge(x, y), listofresults)). \
            assign(
            diff01=lambda x: x.Filter_0 - x.Filter_1,
            diff02=lambda x: x.Filter_0 - x.Filter_2,
            diff03=lambda x: x.Filter_0 - x.Filter_3,
            diff04=lambda x: x.Filter_0 - x.Filter_4,
            mean01=lambda x: (x.Filter_0 + x.Filter_1) / 2,
            mean02=lambda x: (x.Filter_0 + x.Filter_2) / 2,
            mean03=lambda x: (x.Filter_0 + x.Filter_3) / 2,
            mean04=lambda x: (x.Filter_0 + x.Filter_4) / 2,
        )

    def sumInterval(self, experiment=None):
        if experiment is None:

           results = self.filterdata.\
                pivot_table(
                    index=['Exercise', 'interval', 'experiments', 'variable'],
                    values=['Filter_0', 'Filter_1', 'Filter_2', 'Filter_3', 'Filter_4'],
                    aggfunc=[np.mean, np.std]
                )

        self.sumData = results

    def getDelta(self, start=0, end=6):
        deltadata = self.filterdata. \
                        pivot_table(index=['Subject', 'Exercise', 'experiments', 'variable'],
                                    columns='interval',
                                    values=['Filter_0', 'Filter_1', 'Filter_2', 'Filter_3', 'Filter_4']). \
                        dropna(how='all', axis=1)

        delta = {}
        for f in ['Filter_0', 'Filter_1', 'Filter_2', 'Filter_3', 'Filter_4']:
            delta[f] = deltadata[f][end] - deltadata[f][start]

        self.deltadata = pd.DataFrame.from_dict(delta)

    def grapDelta(self, experiment, field):

        g = sns.factorplot(
            x='Exercise',
            y='value',
            hue='Exercise',
            kind='box',
            col='variable',
            palette={'AIT': "#E92323", 'MIT': "#0037F6", 'LIT': "#58F520"},
            order=['AIT', 'MIT', 'LIT'],
            hue_order=['AIT', 'MIT', 'LIT'],
            col_wrap=3,
            data=self.deltadata. \
                reset_index(). \
                rename(columns={'variable': 'field'}). \
                melt(id_vars=['Subject', 'Exercise', 'experiments', 'field']). \
                query('experiments == "{}" & field == "{}"'.format(experiment, field))
        )
        g.set_xlabels('Exercise')
        g.set_ylabels('Delta Change (6-0)')

        return g

    def grapChange(self, experiment, field):

        data = self.filterdata[['Subject', 'Exercise', 'interval', 'experiments', 'variable',
                                  'Filter_0', 'Filter_1', 'Filter_2', 'Filter_3', 'Filter_4']]. \
                reset_index(). \
                rename(columns={'variable': 'field'}). \
                melt(id_vars=['Subject', 'Exercise', 'experiments', 'field', 'interval', 'index']). \
                query('experiments == "{}" & field == "{}"'.format(experiment, field)). \
                rename(columns={'variable': 'filter'})



        g = sns.FacetGrid(data,
                          col='filter',
                          row='Exercise',
                          hue='Exercise',
                          palette=self.palette,
                          xlim=(0,6))
        g.map(plt.plot, 'interval', 'value',linestyle='--')
        g.set_ylabels(field)

        return g


    def anovaResults(self, sort_by=None):

        aovresults = []

        experiments = ['Allo Virtual', 'AlloEgo Virtual', 'Ego Virtual']
        fields = ['Duration', 'PathLength', 'TotalError']
        filters = ['Filter_0', 'Filter_1', 'Filter_2', 'Filter_3', 'Filter_4']
        for exp, field, filter in product(experiments, fields, filters):
            data = self.deltadata. \
                reset_index(). \
                rename(columns={'variable': 'field'}). \
                melt(id_vars=['Subject', 'Exercise', 'experiments', 'field']). \
                query('experiments == "{}" & field == "{}" & variable =="{}"'.format(exp, field, filter)). \
                dropna()
            deltamodel = ols('value~Exercise', data=data).fit()
            table = sm.stats.anova_lm(deltamodel, typ=2)
            table['experiment'] = exp
            table['field'] = field
            table['filter'] = filter
            aovresults.append(table)

        if sort_by is None:
            results = pd.concat(aovresults). \
                loc['Exercise']. \
                sort_values(by='PR(>F)')

        elif sort_by == 'group':
            results = pd.concat(aovresults). \
                loc['Exercise']. \
                groupby(['experiment', 'field', 'filter']). \
                apply(lambda x: x.sort_values(by='PR(>F)'))

        return results


def applyFilter(df, errorfile, filter_type=0):
    aFilter = amunetFilter(df=df, errorfile=errorfile, index=amunetindex)

    if filter_type > 0:
        aFilter.BYerrors()
        aFilter.BYclinicanerrors()

        if filter_type == 2:
            # keeps trials 2-8
            aFilter.BYtrial(omit=[1])
        elif filter_type == 3:
            # keeps trials 5-8
            aFilter.BYtrial(omit=[1, 2, 3, 4])
        elif filter_type == 4:
            # keeps trials 1,2,3 - hardest filter
            aFilter.BYtrial(omit=[4, 5, 6, 7, 8])
        elif filter_type > 4:
            print('Choose 0 - 3 filters')


    return aFilter.df


# RUN -----------------------------------------------------------------
if __name__ == "__main__":
    ###

    parser = argparse.ArgumentParser(prog="Amunet Filter",
                                     description="Filters and analyses amunet data from amunetParser_new.py")
    parser.add_argument('--filedir', help='Specify the directory of the amunet raw data file', action='store',
                        default='C:\\Users\\uqaho4\\Desktop\\hMWM\\Batches')
    parser.add_argument('--filename', help='Specify the filename of the raw amunet file', action='store',
                        default='batch_NoFilter_2019-01-24.csv')
    parser.add_argument('--outdir', help='Specify output dir for results', action='store',
                        default='C:\\Users\\uqaho4\\Desktop\\hMWM\\Results')
    parser.add_argument('--errorfile', help='specify the path to the error file which contains the clinician errors',
                        action='store', default="C:\\Users\\uqaho4\\Desktop\\hMWM\\errors_template.csv")

    parser.add_argument('--analyse', help='specify the analysis to be run', action='store')

    args = parser.parse_args()

    inputdir = args.filedir
    filename = args.filename
    errorfile = args.errorfile

    amunet = amunetAnalysis(inputdir=inputdir, filename=filename, errorfile=errorfile)

    if args.analyse == 'print-sum':
        result = amunet.filterdata.\
                    pivot_table(index=['Exercise', 'interval', 'experiments', 'variable'],
                                values=['Filter_' + str(i) for i in range(0,5)],
                                aggfunc=[max, min]
                                )
        print(result)

    elif args.analyse == 'print-filtered':
        result = amunet.filterdata
        print(result)
        result.to_csv(r'C:\Users\uqaho4\Desktop\Opex Report\Data\filteredamunet.csv')

    elif args.analyse == 'graph-delta':

        run_one = str(eval(input('Run one? (y/n)' )))
        if run_one == 'y':
            experiment = str(eval(input('Choose experiment: ')))
            field = eval(input('Choose field: (Duration, PathLength, TotalError) '))

            from matplotlib import pyplot
            a4_dims = (11.7, 100)
            fig, ax = pyplot.subplots(figsize=a4_dims)
            pfile = 'PLOT_' + experiment + '_' + field + '_' + datetime.today().strftime("%Y-%m-%d") + '.png'
            p = amunet.grapDelta(experiment=experiment, field=field)
            p.show()
            p.savefig(join(args.outdir, pfile))

        elif run_one == 'n':

            for exp, field in product(key_experiments, key_fields):
                a4_dims = (11.7, 100)
                fig, ax = plt.subplots(figsize=a4_dims)
                pfile = 'PLOT_' + exp + '_' + field + '_' + datetime.today().strftime("%Y-%m-%d") + '.png'
                p = amunet.grapDelta(experiment=exp, field=field)
                p.savefig(join(args.outdir, pfile))

    elif args.analyse == 'graph-change':

        run_one = str(eval(input('Run one? (y/n)')))
        if run_one == 'y':
            experiment = str(eval(input('Choose experiment: ')))
            field = eval(input('Choose field: (Duration, PathLength, TotalError) '))

            from matplotlib import pyplot

            a4_dims = (11.7, 100)
            fig, ax = pyplot.subplots(figsize=a4_dims)
            pfile = 'CHANGE_' + experiment + '_' + field + '_' + datetime.today().strftime("%Y-%m-%d") + '.png'
            p = amunet.grapChange(experiment=experiment, field=field)
            p.show()
            p.savefig(join(args.outdir, pfile))

        elif run_one == 'n':

            for exp, field in product(key_experiments, key_fields):
                a4_dims = (11.7, 100)
                fig, ax = plt.subplots(figsize=a4_dims)
                pfile = 'CHANGE_' + exp + '_' + field + '_' + datetime.today().strftime("%Y-%m-%d") + '.png'
                p = amunet.grapChange(experiment=exp, field=field)
                p.savefig(join(args.outdir, pfile))



    elif args.analyse == 'anova':
        sortby = eval(input('Sort by group? (y/n)'))
        result = amunet.anovaResults(sort_by='group')
        print(result)

        save = str(eval(input("Save to file? (y/n)")))

        if save == 'y':
            aovfile = 'AOV_' + datetime.today().strftime("%Y-%m-%d") + '.csv'
            result.to_csv(join(args.outdir, aovfile))


