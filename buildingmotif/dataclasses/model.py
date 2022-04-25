from dataclasses import dataclass
from typing import Optional

import rdflib

from buildingmotif.building_motif import BuildingMotif
from buildingmotif.utils import get_building_motif


@dataclass
class Model:
    """Model. This class mirrors DBModel."""

    _id: int
    _name: str
    graph: rdflib.Graph
    _bm: BuildingMotif

    @classmethod
    def create(cls, name: str) -> "Model":
        """create new Model

        :param name: new model name
        :type name: str
        :return: new Model
        :rtype: Model
        """
        bm = get_building_motif()
        db_model = bm.table_con.create_db_model(name)
        graph = bm.graph_con.create_graph(db_model.graph_id, rdflib.Graph())

        return cls(_id=db_model.id, _name=db_model.name, graph=graph, _bm=bm)

    @classmethod
    def load(cls, id: int) -> "Model":
        """Get Model from db by id

        :param id: model id
        :type id: int
        :return: Model
        :rtype: Model
        """
        bm = get_building_motif()
        db_model = bm.table_con.get_db_model(id)
        graph = bm.graph_con.get_graph(db_model.graph_id)

        return cls(_id=db_model.id, _name=db_model.name, graph=graph, _bm=bm)

    @property
    def id(self) -> Optional[int]:
        return self._id

    @id.setter
    def id(self, new_id):
        raise AttributeError("Cannot modify db id")

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, new_name: str):
        self._bm.table_con.update_db_model_name(self._id, new_name)
        self._name = new_name

    def save_graph(self) -> None:
        """Save graph to db"""
        db_model = self._bm.table_con.get_db_model(self._id)
        self._bm.graph_con.update_graph(db_model.graph_id, self.graph)