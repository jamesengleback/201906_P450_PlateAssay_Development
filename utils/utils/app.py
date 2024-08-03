import os
import base64
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import numpy as np
import pandas as pd
from flask import Flask, render_template, request, url_for
from .model import Result, Well

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/summary', methods=['GET'])
def summary():
    # assert os.path.exists(app.get('db'))
    SQLITE_URI = 'sqlite:///'
    db_uri = SQLITE_URI + os.path.abspath(app.db)
    engine = create_engine(db_uri, echo=True)
    with Session(engine) as session:
        con = session.connection()
        df = pd.read_sql('select * from results where fig is not null limit 12', con)

        count = session.query(Result).count()

    match request.args.get('fmt'):
        case 'json':
            return df.to_json(index=False)

    # x = df['fig'][0]
    # import ipdb ; ipdb.set_trace()
    df = df.replace((None, np.nan), '')
    #x = base64.b64encode(df['fig'][0])
    fn = lambda b : f'<img class="table-fig" src="data:image/png;base64,{str(base64.b64encode(b).decode())}" >' 
    df['fig'] = df['fig'].apply(fn)
    column_order = ['ligand', 'km', 'vmax', 'rsq', 'experiment_number', "fig"]
    df_ = df.loc[:, column_order]
    df.columns = [i.replace('_', ' ').capitalize() for i in df.columns]
    # formatters = {
    #         i: lambda s : f'{s:.1}' for i in df.columns if df[i].dtype == float
    #              }
    html = render_template('summary-table.html',
                           data=df_.to_html(index=False,
                                            float_format=lambda s : f'{s:.1f}',
                                            escape=False,
                                            ),
                           count=count,
                           )
    return html
