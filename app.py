#!/usr/bin/env python
# -*- coding: utf-8 -*-

# core python stuff
import os
from dateutil.relativedelta import relativedelta
import datetime

# Dash/Plotly stuff
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go

# 1010data stuff OMG PLEASE PUT IT UP ON PyPI!!!
try:
    import py1010
except ImportError:
    import urllib
    import platform
    import zipfile
    import sys
    urllib.urlretrieve ('https://www2.1010data.com/downloads/tools/python/py1010.zip', 'py1010.zip')
    # Get site-packages path
    for path in sys.path:
        if '/lib/python2.7/site-packages' in path:
            packagespath = path
    with zipfile.ZipFile('py1010.zip','r') as zf:
        for zfinfo in zf.infolist():
            print zfinfo.filename
            if platform.system() == 'Darwin' and '/bin/osx/2.7/py1010.so' in zfinfo.filename:
                if zfinfo.filename[-1] == '/':
                    continue
                zfinfo.filename = os.path.basename(zfinfo.filename)
                print zf.extract(zfinfo, path=packagespath)
            if platform.system() == 'Linux' and '/bin/lin64/U4-2.7/py1010.so' in zfinfo.filename:
                if zfinfo.filename[-1] == '/':
                    continue
                zfinfo.filename = os.path.basename(zfinfo.filename)
                print zf.extract(zfinfo, path=packagespath)
    import py1010

# other 3rd party stuff
from jinja2 import Template
import pandas as pd
import colorlover as cl



app = dash.Dash('My App')
here = os.path.dirname(__file__)
server = app.server

colorscale = cl.scales['3']['qual']['Set2']

def create_1010_session():
    mygateway = "https://www2.1010data.com/cgi-bin/gw"
    try: 
        myusername = os.environ['TENTEN_USERNAME']
    except KeyError:
        print 'Set a TENTEN_USERNAME!'
    try:
        mypassword = os.environ['TENTEN_PASSWORD']
    except KeyError:
        print 'Set a TENTEN_PASSWORD!'
    mysession = py1010.Session(mygateway, myusername, mypassword, py1010.POSSESS)
    return mysession

def getDateRange(mysession):
    xml_macro = r'''
<colord cols="date"/>
<sel value="g_first1(date;;)"/>
    '''
    myquery = mysession.query('retaildemo.retail.sales_detail', xml_macro)
    myquery.run()
    available_dates = [x[0] for x in myquery.rows]
    return (min(available_dates), max(available_dates))

def last_day_of_month(any_day):
    next_month = any_day.replace(day=28) + datetime.timedelta(days=4)  # this will never fail
    return next_month - datetime.timedelta(days=next_month.day)

def getStores(mysession):
    xml_macro = r'''
<colord cols="store, address, city, state, zip"/>
    '''
    myquery = mysession.query('retaildemo.retail.stores', xml_macro)
    myquery.run()
    return [dict(label=' '.join([str(y) for y in x[1:]]), value=x[0]) for x in myquery.rows]

def getStoreLatLong(mysession, store):
    xml_macro = Template(r'''
<sel value="store={{ store }}"/>
<colord cols="latitude, longitude, address"/>
    ''').render(store=store)
    myquery = mysession.query('retaildemo.retail.stores', xml_macro)
    myquery.run()
    x = myquery.rows[0]
    return dict(lat=x[0], long=x[1], address=x[2])

mysession = create_1010_session()

app.layout = html.Div([
    html.Div([
        html.Img(src='https://1010data.com/img/logo.svg', style=dict(height=35, float='center')),
        html.Div([
            dcc.DatePickerRange(
                    id='daterange',
                    min_date_allowed=getDateRange(mysession)[0],
                    max_date_allowed=getDateRange(mysession)[1],
                    initial_visible_month=datetime.datetime(2014,1,1),
                    start_date=datetime.datetime(2014,1,1),
                    end_date=datetime.datetime(2014,1,31)
                )
        ]),
        html.Div([
            dcc.Dropdown(
                id='store-dropdown',
                options=getStores(mysession)
            )
        ]),
        html.Div([
            dcc.Dropdown(
                id='department-dropdown'
            )
        ]),
        html.Div([
            dcc.Dropdown(
                id='category-dropdown'
            )
        ])
    ], className='three columns'),
    html.Div(id='graphs', className='nine columns', style=dict(margin=10))

], style=dict(textAlign='center'))

@app.callback(
    dash.dependencies.Output('department-dropdown', 'options'),
    [
        dash.dependencies.Input('store-dropdown', 'value'),
        dash.dependencies.Input('daterange', 'start_date'),
        dash.dependencies.Input('daterange', 'end_date')
    ]
)
def set_department_options(selected_store, start_date, end_date):
    if None in [selected_store]:
        return [None]
    print selected_store
    print start_date, end_date
    xml_macro = Template(r'''
<base table="retaildemo.retail.sales_detail"/>
<sel value="between(date;{{ start_date }};{{ end_date }})"/>
<sel value="store={{ selected_store }}"/>
<link table2="retaildemo.retail.products" col="sku"/>
<colord cols="dept, deptdesc"/>
<tabu breaks="dept, deptdesc"/>
    ''').render(selected_store=selected_store, start_date=start_date.replace('-',''), end_date=end_date.replace('-',''))
    print xml_macro
    myquery = mysession.query('retaildemo.retail.sales_detail', xml_macro)
    myquery.run()
    return [dict(label=x[1], value=x[0]) for x in myquery.rows]

@app.callback(
    dash.dependencies.Output('category-dropdown', 'options'),
    [
        dash.dependencies.Input('store-dropdown', 'value'),
        dash.dependencies.Input('daterange', 'start_date'),
        dash.dependencies.Input('daterange', 'end_date'),
        dash.dependencies.Input('department-dropdown', 'value')     
    ]
)
def set_category_options(selected_store, start_date, end_date, selected_department):
    if None in [selected_store, start_date, end_date, selected_department]:
        return [None]
    print selected_store, selected_department
    print start_date, end_date
    xml_macro = Template(r'''
<base table="retaildemo.retail.sales_detail"/>
<sel value="between(date;{{ start_date }};{{ end_date }})"/>
<sel value="store={{ selected_store }}"/>
<link table2="retaildemo.retail.products" col="sku"/>
<sel value="dept={{ selected_department }}"/>
<colord cols="category, categorydesc"/>
<tabu breaks="category, categorydesc"/>
    ''').render(selected_store=selected_store, start_date=start_date.replace('-',''), end_date=end_date.replace('-',''), selected_department=selected_department)
    print xml_macro
    myquery = mysession.query('retaildemo.retail.sales_detail', xml_macro)
    myquery.run()
    return [dict(label=x[1], value=x[0]) for x in myquery.rows]

@app.callback(
    dash.dependencies.Output('graphs','children'),
    [
        dash.dependencies.Input('store-dropdown', 'value'),
        dash.dependencies.Input('daterange', 'start_date'),
        dash.dependencies.Input('daterange', 'end_date'),
        dash.dependencies.Input('department-dropdown', 'value'),
        dash.dependencies.Input('category-dropdown', 'value')    
    ]
)
def update_grid(selected_store, start_date, end_date, selected_department, selected_category):
    children_to_return = []
    print selected_store, selected_department, selected_category
    print start_date, end_date
    if None in [selected_store, start_date, end_date, selected_department, selected_category]:
        return 'Make a selection'
    xml_macro = Template(r'''
<base table="retaildemo.retail.sales_detail"/>
<sel value="between(date;{{ start_date }};{{ end_date }})"/>
<sel value="store={{ selected_store }}"/>
<link table2="retaildemo.retail.products" col="sku" col2="sku" shift="0"/>
<link table2="retaildemo.retail.stores" col="store" col2="store" shift="0"/>
<sel value="dept={{ selected_department }}"/>
<sel value="category={{ selected_category }}"/>
<willbe name="profit" value="xsales-cost" format="type:currency"/>
<tabu breaks="brand">
	<tcol name="sales" source="xsales" fun="sum"/>
	<tcol name="quantity" source="qty" fun="sum"/>
	<tcol name="profit" source="profit" fun="sum"/>
</tabu>
    ''').render(selected_store=selected_store, start_date=start_date.replace('-',''), end_date=end_date.replace('-',''), selected_department=selected_department, selected_category=selected_category)
    print xml_macro
    myquery = mysession.query('retaildemo.retail.sales_detail', xml_macro)
    myquery.run()
    pdf_query = pd.DataFrame({k : list(v) for k, v in myquery.coldict.items()})
    x_bar = pdf_query['brand'].tolist()
    brand_colors = cl.interp(cl.scales['11']['qual']['Paired'],20)[:len(x_bar)]
    print pdf_query.groupby(['brand'])['sales'].agg('sum').tolist()
    store_dict = getStoreLatLong(mysession, selected_store)
    print store_dict

    mapbox_data = [
        go.Scattermapbox(
            lat=[store_dict['lat']],
            lon=[store_dict['long']],
            mode='markers',
            marker=dict(
                size=14
            ),
            text=[store_dict['address']],
        )
    ]
    mapbox_layout = go.Layout(
        autosize=True,
        hovermode='closest',
        mapbox=dict(
            accesstoken=os.environ['MAPBOX_API'],
            bearing=0,
            center=dict(
                lat=store_dict['lat'],
                lon=store_dict['long']
            ),
            pitch=0,
            zoom=12
        ),
    )

    children_to_return.append(
        html.Div([
            html.Div([
                html.H6('Location'),
                dcc.Graph(
                    figure=go.Figure(
                        data=mapbox_data,
                        layout=mapbox_layout
                    ),
                    id='store-mapbox',
                    style=dict(width='100%', height='100%')
                )
            ], className='six columns'),
            html.Div([
                html.H6('Location Market Share'),
                dcc.Graph(
                    #figure = go.Pie(labels=x_bar, values=pdf_query.groupby(['brand'])['sales'].agg('sum').tolist()),
                    figure = go.Figure(
                        data = [
                            go.Pie(
                                labels=x_bar,
                                values=pdf_query.groupby(['brand'])['sales'].agg('sum').tolist(),
                                marker=dict(colors=brand_colors)
                            )
                        ]
                    ),
                    id='store-marketsharepie'
                )
            ], className='six columns')
        ], className='container')
    )
    children_to_return.append(
        html.Div([
            dcc.Graph(
                figure=go.Figure(
                    data=[
                        go.Bar(
                            x=x_bar,
                            y=pdf_query['sales'].tolist(),
                            name='Sales',
                            marker=go.Marker(
                                color=colorscale[0]
                            )
                        ),
                        go.Bar(
                            x=x_bar,
                            y=pdf_query['profit'].tolist(),
                            name='Profit',
                            marker=go.Marker(
                                color=colorscale[1]
                            )
                        )
                    ],
                    layout=go.Layout(
                        title='Brand Metrics',
                        showlegend=True,
                        legend=go.Legend(
                            x=1.0,
                            y=1.0
                        ),
                        yaxis=dict(title='$'),
                        margin=go.Margin(l=40, r=0, t=40, b=30)
                    )
                ),
                #style={'height': 300},
                id='my-graph'
            )
        ])
    )
    return children_to_return

app.css.append_css({
    'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'
})

if __name__ == '__main__':
    app.run_server(debug=True)
