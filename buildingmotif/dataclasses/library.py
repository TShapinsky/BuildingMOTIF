import logging
import pathlib
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional

import rdflib
import yaml
from rdflib.util import guess_format

from buildingmotif import get_building_motif
from buildingmotif.database.tables import DBTemplate
from buildingmotif.dataclasses.shape_collection import ShapeCollection
from buildingmotif.dataclasses.template import Template
from buildingmotif.template_compilation import compile_template_spec
from buildingmotif.utils import get_template_parts_from_shape

if TYPE_CHECKING:
    from buildingmotif import BuildingMOTIF


@dataclass
class _template_dependency:
    """
    Represents early-bound (template_id) or late-bound (template_name + library)
    dependency of a template on another template.
    """

    template_name: str
    bindings: Dict[str, Any]
    library: str
    template_id: Optional[int] = None

    def __repr__(self):
        return (
            f"dep<name={self.template_name} bindings={self.bindings} "
            "library={self.library} id={self.template_id}>"
        )

    @classmethod
    def from_dict(
        cls, d: Dict[str, Any], dependent_library_name: str
    ) -> "_template_dependency":
        template_name = d["template"]
        bindings = d.get("args", {})
        library = d.get("library", dependent_library_name)
        template_id = d.get("template_id")
        return cls(template_name, bindings, library, template_id)

    def to_template(self, id_lookup: Dict[str, int]) -> Template:
        """
        Resolve this dependency to a Template

        :param id_lookup: a local cache of name -> id for uncommitted templates
        :type id_lookup: Dict[str, int]
        :return: the Template instance this dependency points to
        :rtype: Template
        """
        # direct lookup if id is provided
        if self.template_id is not None:
            return Template.load(self.template_id)
        # if id is not provided, look at our local 'cache' of to-be-committed
        # templates for the id (id_lookup)
        if self.template_name in id_lookup:
            return Template.load(id_lookup[self.template_name])
        # if not in the local cache, then search the database for the template
        # within the given library
        library = Library.load(name=self.library)
        return library.get_template_by_name(self.template_name)


@dataclass
class Library:
    """Collection of shapes and templates. This class mirrors DBLibrary."""

    _id: int
    _name: str
    _bm: "BuildingMOTIF"

    @classmethod
    def create(cls, name: str) -> "Library":
        """Create new Library.

        :param name: library name
        :type name: str
        :return: new Library
        :rtype: "Library"
        """
        bm = get_building_motif()
        db_library = bm.table_connection.create_db_library(name)

        return cls(_id=db_library.id, _name=db_library.name, _bm=bm)

    # TODO: load library from URI? Does the URI identify the library uniquely?
    @classmethod
    def load(
        cls,
        db_id: Optional[int] = None,
        ontology_graph: Optional[str] = None,
        directory: Optional[str] = None,
        name: Optional[str] = None,
    ) -> "Library":
        """
        Loads a Library from the database or an external source.

        :param db_id: the unique id of the library in the database, defaults to None
        :type db_id: Optional[int], optional
        :param ontology_graph: a path to a serialized RDF graph, defaults to None
        :type ontology_graph: Optional[str], optional
        :param directory: a path to a directory containing a library, defaults to None
        :type directory: Optional[str], optional
        :param name: the name of the library inside the database, defaults to None
        :type name: Optional[str], optional
        :return: the loaded library
        :rtype: "Library"
        :raises Exception: if the library cannot be loaded
        """
        if db_id is not None:
            return cls._load_from_db(db_id)
        elif ontology_graph is not None:
            ontology = rdflib.Graph()
            ontology.parse(ontology_graph, format=guess_format(ontology_graph))
            return cls._load_from_ontology_graph(ontology)
        elif directory is not None:
            src = pathlib.Path(directory)
            if not src.exists():
                raise Exception(f"Directory {src} does not exist")
            return cls._load_from_directory(src)
        elif name is not None:
            bm = get_building_motif()
            db_library = bm.table_connection.get_db_library_by_name(name)
            return cls(_id=db_library.id, _name=db_library.name, _bm=bm)
        else:
            raise Exception("No library information provided")

    @classmethod
    def _load_from_db(cls, id: int) -> "Library":
        """Load Library from database.

        :param id: id of library
        :type id: int
        :return: Library
        :rtype: "Library"
        """
        bm = get_building_motif()
        db_library = bm.table_connection.get_db_library_by_id(id)

        return cls(_id=db_library.id, _name=db_library.name, _bm=bm)

    @classmethod
    def _load_from_ontology_graph(cls, ontology: rdflib.Graph) -> "Library":
        """Load a library from an ontology graph. This proceeds as follows.
        First, get all entities in the graph that are instances of *both* owl:Class
        and sh:NodeShape. (this is "candidates")

        For each candidate, use the utility function to parse the NodeShape and turn
        it into a Template.
        """
        # TODO: handle shapes (eventually)

        # get the name of the ontology; this will be the name of the library
        # any=False will raise an error if there is more than one ontology defined  in the graph
        ontology_name = ontology.value(
            predicate=rdflib.RDF.type, object=rdflib.OWL.Ontology, any=False
        )
        # create the library
        lib = cls.create(ontology_name)
        class_candidates = set(ontology.subjects(rdflib.RDF.type, rdflib.OWL.Class))
        shape_candidates = set(ontology.subjects(rdflib.RDF.type, rdflib.SH.NodeShape))
        candidates = class_candidates.intersection(shape_candidates)

        # stores the lookup from template *names* to template *ids*
        # this is necessary because while we know the *name* of the dependee templates
        # for each dependent template, we don't know the *id* of the dependee templates,
        # which is necessary to populate the dependencies
        template_id_lookup: Dict[str, int] = {}
        dependency_cache: Dict[int, List[Dict[Any, Any]]] = {}
        for candidate in candidates:
            assert isinstance(candidate, rdflib.URIRef)
            partial_body, deps = get_template_parts_from_shape(candidate, ontology)
            templ = lib.create_template(str(candidate), partial_body)
            dependency_cache[templ.id] = deps
            template_id_lookup[str(candidate)] = templ.id

        # now that we have all the templates, we can populate the dependencies
        for template in lib.get_templates():
            if template.id not in dependency_cache:
                continue
            for dep in dependency_cache[template.id]:
                if dep["template"] in template_id_lookup:
                    dependee = Template.load(template_id_lookup[dep["template"]])
                    template.add_dependency(dependee, dep["args"])
                else:
                    logging.warn(f"Warning: could not find dependee {dep['template']}")
        return lib

    @classmethod
    def _load_from_directory(cls, directory: pathlib.Path) -> "Library":
        """
        Load a library from a directory. Templates are read from .yml files
        in the directory. The name of the library is given by the name of the directory.
        """
        # TODO: handle shapes (eventually)

        lib = cls.create(directory.name)
        template_id_lookup: Dict[str, int] = {}
        dependency_cache: Dict[int, List[_template_dependency]] = {}
        # read all .yml files
        for file in directory.rglob("*.yml"):
            contents = yaml.load(open(file, "r"), Loader=yaml.FullLoader)
            for templ_name, templ_spec in contents.items():
                # compile the template body using its rules
                templ_spec = compile_template_spec(templ_spec)
                # input name of template
                templ_spec.update({"name": templ_name})
                # remove dependencies so we can resolve them to their IDs later
                deps = [
                    _template_dependency.from_dict(d, lib.name)
                    for d in templ_spec.pop("dependencies", [])
                ]
                templ_spec["optional_args"] = templ_spec.pop("optional", [])
                try:
                    templ = lib.create_template(**templ_spec)
                except Exception as e:
                    logging.error(
                        f"Error creating template {templ_name} from file {file}: {e}"
                    )
                    raise e
                dependency_cache[templ.id] = deps
                template_id_lookup[templ.name] = templ.id
        # now that we have all the templates, we can populate the dependencies
        for template in lib.get_templates():
            if template.id not in dependency_cache:
                continue
            for dep in dependency_cache[template.id]:
                try:
                    dependee = dep.to_template(template_id_lookup)
                    template.add_dependency(dependee, dep.bindings)
                except Exception as e:
                    logging.warn(f"Warning: could not resolve dependency {dep}")
                    raise e
        return lib

    @property
    def id(self) -> Optional[int]:
        return self._id

    @id.setter
    def id(self, new_id):
        raise AttributeError("Cannot modify db id")

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, new_name: str):
        self._bm.table_connection.update_db_library_name(self._id, new_name)
        self._name = new_name

    def create_template(
        self,
        name: str,
        body: Optional[rdflib.Graph] = None,
        optional_args: Optional[List[str]] = None,
    ) -> Template:
        """Create Template in this Library.

        :param name: name
        :type name: str
        :param body: template body
        :type body: rdflib.Graph
        :param optional_args: optional parameters for the template
        :type optional_args: list[str]
        :return: created Template
        :rtype: Template
        """
        db_template = self._bm.table_connection.create_db_template(name, self._id)
        body = self._bm.graph_connection.create_graph(
            db_template.body_id, body if body else rdflib.Graph()
        )
        if optional_args is None:
            optional_args = []
        self._bm.table_connection.update_db_template_optional_args(
            db_template.id, optional_args
        )

        return Template(
            _id=db_template.id,
            _name=db_template.name,
            body=body,
            optional_args=optional_args,
            _bm=self._bm,
        )

    def get_templates(self) -> List[Template]:
        """Get Templates from Library.

        :return: list of templates
        :rtype: list[Template]
        """
        db_library = self._bm.table_connection.get_db_library_by_id(self._id)
        templates: List[DBTemplate] = db_library.templates
        return [Template.load(t.id) for t in templates]

    def get_shape_collection(self) -> ShapeCollection:
        """Get Shape Collection from Library.

        :return: library's shape collection
        :rtype: ShapeCollection
        """
        db_library = self._bm.table_connection.get_db_library_by_id(self._id)

        return ShapeCollection.load(db_library.shape_collection.id)

    def get_template_by_name(self, name: str) -> Template:
        """
        Get Template by name from Library.
        """
        dbt = self._bm.table_connection.get_db_template_by_name(name)
        if dbt.library_id != self._id:
            raise ValueError(f"Template {name} not in library {self._name}")
        return Template.load(dbt.id)
