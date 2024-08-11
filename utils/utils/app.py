import os
import re
import base64
import json
from textwrap import dedent
from sqlalchemy import create_engine, update
from sqlalchemy.orm import Session
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, url_for, redirect
from .model import Result, Well, ResultComment
from .cli import TextStyle

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
    experiment_number = request.args.get('experiment-number')
    ligand = request.args.get('ligand')
    volume = request.args.get('volume')
    concentration = request.args.get('concentration')

    engine = create_engine(DB_URI, echo=True)
    with Session(engine) as session:
        query = session.query(Result)
        if experiment_number:
            query = query.where(Result.experiment_number == int(experiment_number))
        if ligand:
            query = query.where(Result.ligand == ligand)
        if volume:
            query = query.where(Result.volume == volume)
        if concentration:
            query = query.where(Result.protein_concentration == concentration)

        query = query.order_by(Result.experiment_number, Result.id).offset(page * PAGE_SIZE).limit(PAGE_SIZE)

        df = pd.read_sql(query.statement, session.bind)

        count = session.query(Result).count()
    if page * PAGE_SIZE > count:
        return '', 204

    match format:
        case 'json':
            return df.to_json(index=False)


    # df['uri'] = df['id'].apply(lambda id: f'result/{id}')
    df['uri'] = df['id'].apply(lambda id: f"<button hx-get='result/{id}' hx-target='#hud' hx-swap='outerHTML'>result/{id}</button>")
    column_order = ['experiment_number', 'ligand', 'well_volume', 'volume', 'protein_concentration', 'km', 'vmax', 'rsq', 'uri']
    df_ = df.loc[:, column_order]
    df_.columns = [i.replace('_', ' ').capitalize() for i in df_.columns]
    df_.fillna('', inplace=True)
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
    current_url_params = '&'.join([f'{i}={request.args[i]}' for i in request.args])
    td = soup.new_tag('td',
                      attrs={'hx-get': f'/summary?page={page + 1}&append&{current_url_params}',
                             'hx-trigger': 'revealed once',
                             'hx-target': '.summary-tbody',
                             'hx-swap': 'beforeend',
                             'colspan': len(df_.columns)
                             })
    #td.string = '...'
    tr = soup.new_tag('tr')
    tr.append(td)
    if soup.tbody is not None:
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
            comments = '; '.join([i for i in [request.form.get('comment'),
                                              request.form.get('comment-dropdown')
                                              ]
                                  if i])
            if comments is not None:
                result_comment = ResultComment(result_id=id,
                                               comment=comments,
                                               )
                session.add(result_comment)
                session.commit()
            # query = session.query(Result).filter(Result.id == id)
            # result = query.first()
            # result.comment = request.form.get('comment')
            # session.add(result)
            # session.commit()

    with Session(engine) as session:
        query = session.query(Result).filter(Result.id == id)
        result = query.first()
        df = pd.read_sql(query.statement, session.connection())

        query_comments = session.query(ResultComment).filter(ResultComment.result_id == id)
        comments = [i.comment for i in query_comments]

        query_wells = session.query(Well).filter(Well.result_id == id)
        query_test_wells = query_wells.filter(Well.control == False)
        query_control_wells = query_wells.filter(Well.control == True)
        df_test_wells = pd.read_sql(query_test_wells.statement, session.connection())
        df_control_wells = pd.read_sql(query_control_wells.statement, session.connection())

        comments_joined = ' '.join([i.comment for i in query_comments])
        # unique_comments = [i[0] for i in
        #                    session.query(Result.comment).distinct().order_by(Result.comment).limit(20)
        #                    if i[0]]

    assert len(df) <= 1, f"Multiple records found for id {id}"
    if len(df) == 0:
        return f'No result {id}'

    df.drop('fig', axis=1, inplace=True)

    experiment_number = df.loc[0, 'experiment_number']
    ligand = df.loc[0, 'ligand']
    km = df.loc[0, 'km']
    vmax = df.loc[0, 'vmax']
    rsq = df.loc[0, 'rsq']

    df.columns = [i.replace('_', ' ').capitalize() for i in df.columns]
    df.fillna('', inplace=True)
    df_html = df.T.to_html(index=True,
                           header=False,
                           float_format=lambda s: f'{s:.1f}',
                           escape=False,
                           classes='hud-table',
                           na_rep='',
                           )

    df_wells = df_test_wells.append(df_control_wells)

    df_wells['comment_html'] = df_wells.apply(lambda x: dedent(f"""
                                         <form class='row' hx-post='well/{x.id}' hx-include='find input'>
                                             <input name='comment' type='text' value='{x.comment}'>
                                             <input type='submit' value='update'>
                                         </form>
                                         """).replace('\n', ' '),
                                         axis=1,
                                         )

    df_wells['exclude_html'] = df_wells.apply(lambda x: dedent(f"""
                                             <input hx-patch='{url_for('well', id=x.id)}' type='checkbox' name='exclude' {'checked' if x.exclude else ''}>
                                         """).replace('\n', ' '),
                                         axis=1,
                                         )

    
    df_wells = df_wells.loc[:, ['id',
                                'result_id',
                                'comment_html',
                                'exclude_html',
                                'address',
                                'ligand',
                                'control',
                                'a_800',
                                'auc',
                                'k',
                                'rsq',
                                'concentration',
                                'volume',
                                'file',
                                ]]

    df_wells.fillna('', inplace=True)

    df_wells_html = df_wells.to_html(float_format=lambda s: f'{s:.1f}',
                                     escape=False,
                                     na_rep='',
                                     classes='well-table',
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
                           #df_wells_html=df_wells_html,
                           )

@app.route('/pulse', methods=['GET'])
def pulse():
    DB_URI = f'sqlite:///{os.path.abspath(app.db)}'
    engine = create_engine(DB_URI, echo=True)

    with Session(engine) as session:
        count = session.query(Result).count()

    #response = {'count': count}
    return str(count)


@app.route('/well/<int:id>', methods=['POST'])
@app.route('/wells', methods=['GET'], defaults={'id':None})
def well(id=None,
         ):
    result_id = request.args.get('result_id')
    DB_URI = f'sqlite:///{os.path.abspath(app.db)}'
    engine = create_engine(DB_URI, echo=True)

    match request.method:
        case 'POST':
            with Session(engine) as session:
                query = session.query(Well).filter(Well.id == id)
                well = query.first()
                result_id = well.result_id
                if (comment:=request.form.get('comment')):
                    well.comment = comment
                if request.form.get('exclude') is not None:
                    well.exclude = True
                else:
                    well.exclude = False
                session.add(well)
                session.commit()
            return redirect(url_for('well', result_id=result_id))
        case 'GET':
            with Session(engine) as session:
                query_wells = session.query(Well).filter(Well.result_id == result_id)
                df_wells = pd.read_sql(query_wells.statement, session.connection())
                df_wells['comment_html'] = df_wells.apply(lambda x: dedent(f"""
<input name='comment' type='text' value='{x.comment if x.comment is not None else ''}' hx-post='well/{x.id}' >
                                                     """).replace('\n', ' '),
                                                     axis=1,
                                                     )

                # <input hx-patch='{url_for('well', id=x.id)}' type='checkbox' name='exclude' {'checked' if x.exclude else ''}>
                df_wells['exclude_html'] = df_wells.apply(lambda x: dedent(f"""
<input hx-post='well/{x.id}' type='checkbox' name='exclude' {'checked' if x.exclude else ''}>
                                                     """).replace('\n', ' '),
                                                     axis=1,
                                                     )

                
                df_wells = df_wells.loc[:, ['id',
                                            'result_id',
                                            'comment_html',
                                            'exclude_html',
                                            'address',
                                            'ligand',
                                            'control',
                                            'a_800',
                                            'auc',
                                            'k',
                                            'rsq',
                                            'concentration',
                                            'volume',
                                            'file',
                                            ]]

                df_wells.fillna('', inplace=True)

                df_wells_html = df_wells.to_html(float_format=lambda s: f'{s:.1f}',
                                                 escape=False,
                                                 na_rep='',
                                                 classes='well-table',
                                                 )

            return df_wells_html, 200
