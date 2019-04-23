import os, json, io, requests
import pandas as pd
import numpy as np
import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# #  NSIDC-0051 Derived FUBU Data Explorer Tool                         # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def load_data():
    # load the data
    url = 'https://www.snap.uaf.edu/webshared/Michael/data/seaice_noaa_indicators/sic_daily_vals.csv'
    s = requests.get(url).content
    df = pd.read_csv(io.StringIO(s.decode('utf-8')), index_col=0, parse_dates=True)
    # df = pd.read_csv('sic_daily_vals.csv', index_col=0, parse_dates=True)
    url = 'https://www.snap.uaf.edu/webshared/Michael/data/seaice_noaa_indicators/winter_threshold_vals.csv'
    s = requests.get(url).content
    threshold = pd.read_csv(io.StringIO(s.decode('utf-8')), index_col=0, parse_dates=True)

    # marks dates
    # load the data
    url = 'https://www.snap.uaf.edu/webshared/Michael/data/seaice_noaa_indicators/barrow_fubu_dates_mark_nosmooth_mledit.csv'
    s = requests.get(url).content
    fubu_mark = pd.read_csv(io.StringIO(s.decode('utf-8')), index_col=0, parse_dates=True)
    # fubu_mark = pd.DataFrame({i:j.fillna(i.strftime('%Y-%m-%d')) for i,j in fubu_mark.iterrows()}).T

    # michaels dates
    url = 'https://www.snap.uaf.edu/webshared/Michael/data/seaice_noaa_indicators/barrow_fubu_dates_michael_nosmooth.csv'
    s = requests.get(url).content
    fubu_mike = pd.read_csv(io.StringIO(s.decode('utf-8')), index_col=0, parse_dates=True)
    fubu_mike = fubu_mike.replace('0000', np.nan)
    # fubu_mike = pd.DataFrame({i:j.fillna(i.strftime('%Y-%m-%d')) for i,j in fubu_mike.iterrows()}).T
    
    return df, threshold, fubu_mark, fubu_mike

# load data
df, threshold, fubu_mark, fubu_mike = load_data()

mdown = '''
'''

app = dash.Dash(__name__)
server = app.server
server.secret_key = os.environ['SECRET-SNAP-KEY']
# server.secret_key = 'secret_key'
app.config.supress_callback_exceptions = True
app.css.append_css({'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'})
app.title = 'SeaIce-FUBU-Utqiagvik'

years = df.index.map(lambda x: x.year).unique().tolist()
years = [i for i in years if i <= 2012]

# # BUILD PAGE LAYOUT
app.layout = html.Div([
                    html.Div([
                        html.H2('Explore NSIDC-0051 Sea Ice Concentration -- Freeze/Break-Up'),
                        html.H4('Utqiagvik (Barrow) Test Case Site (paper data)'),
                        ]),
                    html.Div([
                        html.Div([dcc.Graph( id='my-graph' ) ] ),
                        html.Div([
                            dcc.Slider(
                                    id='year-slider',
                                    min=min(years),
                                    max=max(years),
                                    value=2007,
                                    marks={str(i):{'label':i} for i in years},
                                    included=False
                                    ),
                        ], className='eleven columns')

                    ])
                ])


def make_scatter_plots_mark( df, df_year, year ):
    metrics = ['breakup_start', 'breakup_end', 'freezeup_start', 'freezeup_end']
    colors = {'breakup_start':'rgb(165, 19, 39)', 'breakup_end':'rgb(68, 8, 16)', \
            'freezeup_start':'rgb(19, 60, 163)', 'freezeup_end':'rgb(8, 25, 68)'}
    done = []
    for metric in metrics:
        val, = df.loc[str(year),metric]
        if not pd.isna(val):
            plot = go.Scatter(
                    x=df[metric],
                    y=df_year.loc[df[metric].values[0]],
                    name=metric+' Mark',
                    text=[metric+' Mark'],
                    mode = 'markers',
                    hoverlabel = dict(namelength=-1),
                    hoverinfo ='x+y+text',
                    marker = dict(
                                size = 7,
                                color = colors[metric],
                                line = dict(
                                    width = 1,
                                    color = colors[metric]
                                )
                            ),                    
                    ),
            done.append(plot[0].to_plotly_json())
    return done

def make_scatter_plots_mike( metric_df, df_year, year ):
    metrics = ['breakup_start', 'breakup_end', 'freezeup_start', 'freezeup_end']
    colors = {'breakup_start':'rgb(249, 184, 99)', 'breakup_end':'rgb(249, 184, 99)', \
            'freezeup_start':'rgb(30, 218, 232)', 'freezeup_end':'rgb(30, 218, 232)'}
    done = []
    for metric in metrics:
        val, = metric_df.loc[str(year),metric]
        if not pd.isna(val):
            plot = go.Scatter(
                    x=metric_df[metric],
                    y=df_year.loc[metric_df[metric].values[0]],
                    name=metric+' Mike',
                    text=[metric+' Mike'],
                    mode = 'markers',
                    hoverlabel = dict(namelength=-1),
                    hoverinfo ='x+y+text',
                    marker = dict(
                                size = 13,
                                color = colors[metric],
                                line = dict(
                                    width = 1,
                                    color = colors[metric]
                                )
                            ),                    
                    ),
            plot[0]['marker']['symbol'] = 'triangle-up'

            done.append(plot[0].to_plotly_json())
    return done

def make_duration_line( metric_df, df_year, year ):
    metrics = [['breakup_start', 'breakup_end'], ['freezeup_start', 'freezeup_end']]

    colors = {'breakup_start':'rgb(165, 19, 39)', 'breakup_end':'rgb(165, 19, 39)', \
            'freezeup_start':'rgb(19, 60, 163)', 'freezeup_end':'rgb(19, 60, 163)'}
    done = []
    for metric_group in metrics:
        vals = metric_df[metric_group]
        if (~pd.isna(vals.reset_index(drop=True)).squeeze()).all():
            df_sub = df_year.loc[metric_df[metric_group[0]].squeeze():metric_df[metric_group[1]].squeeze()]
            plot = go.Scatter(
                    x=df_sub.index,
                    y=df_sub.sic,
                    name=metric_group[0].split('_')[0],
                    mode = 'lines+markers',
                    hoverinfo='skip',
                    marker = dict(
                                size = 1.4,
                                color = colors[metric_group[0]],
                                line = dict(
                                    width = 1,
                                    color = colors[metric_group[0]]
                                )
                            ),
                    ),
            done.append(plot[0].to_plotly_json())
    return done

@app.callback( Output('my-graph', 'figure'), 
            [Input('year-slider', 'value')])
def update_graph( year ):
    # pull data for the year we want to examine
    df_year = df.loc[str(year)].copy()*100
    mark = fubu_mark[str(year)]
    mike = fubu_mike[str(year)]

    # make a plotly json object directly using cufflinks
    title = 'NSIDC-0051 Sea Ice Concentration {}'.format(year)

    plots = [go.Scatter(
                x=df_year.index.tolist(),
                y=df_year.sic.tolist(),
                name='concentration(%)',
                text='concentration(%)',
                mode = 'lines+markers',
                line={'color':'black', 'width':1.2},
                marker={'color':'black', 'size':2.5},
                hoverlabel = dict(namelength=-1),
                hoverinfo ='x+y+text',
                ),] + \
            make_duration_line(mark,df_year,year) + \
            make_scatter_plots_mike(mike,df_year,year) + \
            make_scatter_plots_mark(mark,df_year,year)
            
    layout = { 
                'title': title,
                'xaxis': dict(title='Time'),
                'yaxis': dict(title='% Concentration', range=[0,100], hoverformat='.2f'),
                }
    print('len traces: {}'.format(len(plots) ))

    return {'data':plots,'layout':layout}


if __name__ == '__main__':
    app.run_server( debug=False )
