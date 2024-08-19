import logging
import sqlite3
from sqlalchemy import Column, Float, Integer, String, Boolean, Sequence, LargeBinary, ForeignKey, JSON
from sqlalchemy.orm import declarative_base


Base = declarative_base()


class Result(Base):
    __tablename__ = 'results'
    id = Column(Integer, Sequence('result_id_seq'), primary_key=True)
    experiment_number = Column(Integer)
    centrifuge_minutes = Column(Integer)
    centrifuge_rpm = Column(Integer)
    dispense_bulk = Column(String)
    volume = Column(Integer)
    protein_name = Column(String)
    dispense_ligands = Column(String)
    protein_days_thawed = Column(Integer)
    well_volume = Column(Integer)
    ligand = Column(String)
    protein_concentration = Column(Float)
    plate_type = Column(String)

    k = Column(Float)
    km = Column(Float)
    vmax = Column(Float)
    rsq = Column(Float)
    a420_max = Column(Float)
    auc_mean = Column(Float)
    auc_cv = Column(Float)
    std_405 = Column(Float)
    dd_soret = Column(Float)
    fig = Column(LargeBinary)

    visited = Column(Boolean, default=False)
    ok = Column(Boolean)


class Well(Base):
    __tablename__ = 'wells'
    id = Column(Integer, Sequence('well_id_seq'), primary_key=True)
    result_id = Column(Integer, ForeignKey('results.id'))
    a_800 = Column(Float)
    auc = Column(Float)
    k = Column(Float)
    rsq = Column(Float)
    concentration = Column(Float)
    volume = Column(Float)

    address = Column(String)
    file = Column(String)
    ligand = Column(String)
    control = Column(Boolean)
    comment = Column(String)
    exclude = Column(Boolean, default=False)

    raw_data = Column(JSON)

class ResultComment(Base):
    __tablename__ = 'result_comments'
    id = Column(Integer, Sequence('comment_id_seq'), primary_key=True)
    result_id = Column(Integer, ForeignKey('results.id'))
    comment = Column(String)

def add_data(model_type, session, **kwargs) -> None:
    """ arbitary add allowed feilds to table
    """
    column_names = [i.name for i in model_type.__table__.columns]
    allowed_kwargs = {i:kwargs.get(i) for i in column_names if i != "id"}
    model_item = model_type(**allowed_kwargs)
    session.add(model_item)
    session.commit()
    str_args = [f"{i}={j.__str__()[:32]}" for i, j in zip(allowed_kwargs.keys(), 
                                                        allowed_kwargs.values())
                ]
    logging.info(f"{model_type} ARGS: {str_args}: OK")
    return model_item

