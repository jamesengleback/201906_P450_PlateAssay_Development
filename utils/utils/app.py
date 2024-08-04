import os
import re
import base64
from textwrap import dedent
from sqlalchemy import create_engine, update
from sqlalchemy.orm import Session
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, url_for
from .model import Result, Well

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/summary', methods=['GET'])
def summary():
    # assert os.path.exists(app.get('db'))
    DB_URI = f'sqlite:///{os.path.abspath(app.db)}'
    PAGE_SIZE = 32

    format = request.args.get('fmt')
    page = int(request.args.get('page', 0))
    html_append = request.args.get('append') is not None

    engine = create_engine(DB_URI, echo=True)
    with Session(engine) as session:
        query = session.query(Result).offset(page * PAGE_SIZE).limit(PAGE_SIZE)

        df = pd.read_sql(query.statement, session.bind)

        count = session.query(Result).count()
    if page * PAGE_SIZE > count:
        import ipdb ; ipdb.set_trace()
        pass

    match format:
        case 'json':
            return df.to_json(index=False)


    df['uri'] = df['id'].apply(lambda id: f'result/{id}')
    df['see more'] = df['uri'].apply(lambda uri: f"<button hx-get='{uri}' hx-target='#hud' hx-swap='outerHTML'>{uri}</button>")
    column_order = ['ligand', 'km', 'vmax', 'rsq', 'experiment_number', 'uri', 'see more'] # "fig"]
    df_ = df.loc[:, column_order]
    df_.columns = [i.replace('_', ' ').capitalize() for i in df_.columns]
    df_html = df_.to_html(index=False,
                          float_format=lambda s : f'{s:.1f}',
                          escape=False,
                          na_rep='',
                          classes='summary-table',
                          )

    # add inifinite scroll
    soup = BeautifulSoup(df_html, 'html.parser')
    tr_ = re.search('<tbody>(.*)</tbody>', df_html, re.DOTALL|re.MULTILINE)
    tr = tr_.groups()[0]
    td = soup.new_tag('td',
                      attrs={'hx-get': f'/summary?page={page + 1}&append',
                             'hx-trigger': 'revealed once',
                             'hx-target': '.summary-tbody',
                             'hx-swap': 'beforeend',
                             'colspan': len(df_.columns)
                             })
    td.string = '...'
    tr = soup.new_tag('tr')
    tr.append(td)
    soup.tbody.append(tr)
    soup.tbody['class'] = 'summary-tbody'

    if html_append:
        return ''.join([str(i) for i in soup.tbody.children])

    df_html = str(soup)

    html = render_template('summary-table.html',
                           count=count,
                           data=df_html,
                           page=page,
                           )

    return html

@app.route("/result", methods=["GET", "POST"])
@app.route("/result/<int:id>", methods=["GET", "POST"])
def result(id=None):

    DB_URI = f'sqlite:///{os.path.abspath(app.db)}'
    engine = create_engine(DB_URI, echo=True)

    if request.method == 'POST':
        with Session(engine) as session:
            query = session.query(Result).filter(Result.id == id)
            result = query.first()
            result.comment = request.form.get('comment')
            session.add(result)
            session.commit()

    with Session(engine) as session:
        query = session.query(Result).filter(Result.id == id)
        result = query.first()
        df = pd.read_sql(query.statement, session.connection())

    assert len(df) == 1, f"Multiple records found for id {id}"
    df.drop('fig', axis=1, inplace=True)

    experiment_number = df.loc[0, 'experiment_number']
    ligand = df.loc[0, 'ligand']
    km = df.loc[0, 'km']
    vmax = df.loc[0, 'vmax']
    rsq = df.loc[0, 'rsq']
    comments = df.loc[0, 'comment']

    df.columns = [i.replace('_', ' ').capitalize() for i in df.columns]
    df_html = df.T.to_html(index=True,
                           header=False,
                           float_format=lambda s: f'{s:.1f}',
                           escape=False,
                           classes='hud-table',
                           na_rep='',
                           )

    return render_template('result-summary.html',
                           id=id,
                           df_html=df_html,
                           fig=str(base64.b64encode(result.fig).decode()),
                           experiment_number=experiment_number,
                           ligand=ligand,
                           km=km,
                           vmax=vmax,
                           rsq=rsq,
                           comments=comments,
                           )
