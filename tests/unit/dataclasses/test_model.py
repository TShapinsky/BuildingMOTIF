import pytest
from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.compare import isomorphic
from rdflib.namespace import FOAF

from buildingmotif import BuildingMOTIF
from buildingmotif.dataclasses import Library, Model, ValidationContext
from buildingmotif.namespaces import BRICK, RDF, RDFS, SH, A

BLDG = Namespace("urn:building/")


def test_create_model(clean_building_motif):
    model = Model.create(name="https://example.com", description="a very good model")

    assert isinstance(model, Model)
    assert model.name == "https://example.com"
    assert model.description == "a very good model"
    assert isinstance(model.graph, Graph)


def test_create_model_bad_name(clean_building_motif):
    with pytest.raises(ValueError):
        Model.create(name="I have spaces")

    assert len(clean_building_motif.table_connection.get_all_db_models()) == 0


def test_load_model(clean_building_motif):
    m = Model.create(name="https://example.com", description="a very good model")
    m.graph.add((URIRef("http://example.org/alex"), RDF.type, FOAF.Person))

    result = Model.load(m.id)
    assert result.id == m.id
    assert result.name == m.name
    assert result.description == m.description
    assert isomorphic(result.graph, m.graph)

    # test model_load_by_name
    result = Model.load(name="https://example.com")
    assert result.id == m.id
    assert result.name == m.name
    assert result.description == m.description
    assert isomorphic(result.graph, m.graph)


def test_validate_model(clean_building_motif):
    # load library
    lib = Library.load(ontology_graph="tests/unit/fixtures/shapes/shape1.ttl")
    assert lib is not None

    BLDG = Namespace("urn:building/")
    m = Model.create(name=BLDG)
    m.add_triples((BLDG["vav1"], A, BRICK.VAV))

    ctx = m.validate([lib.get_shape_collection()])
    assert not ctx.valid

    m.add_triples((BLDG["vav1"], A, BRICK.VAV))
    m.add_triples((BLDG["vav1"], BRICK.hasPoint, BLDG["temp_sensor"]))
    m.add_triples((BLDG["temp_sensor"], A, BRICK.Temperature_Sensor))
    m.add_triples((BLDG["vav1"], BRICK.hasPoint, BLDG["flow_sensor"]))
    m.add_triples((BLDG["flow_sensor"], A, BRICK.Air_Flow_Sensor))

    ctx = m.validate([lib.get_shape_collection()])
    assert ctx.valid

    assert len(ctx.diffset) == 0


def test_validate_model_with_failure(bm: BuildingMOTIF):
    """
    Test that a model correctly validates
    """
    shape_graph_data = """
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix brick: <https://brickschema.org/schema/Brick#> .
@prefix : <urn:shape_graph/> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
: a owl:Ontology .
:zone_shape a sh:NodeShape ;
    sh:targetClass brick:HVAC_Zone ;
    sh:message "all HVAC zones must have a label" ;
    sh:property [
        sh:path rdfs:label ;
        sh:minCount 1 ;
    ] .
    """
    shape_graph = Graph().parse(data=shape_graph_data)
    shape_lib = Library.load(ontology_graph=shape_graph)

    lib = Library.load(directory="tests/unit/fixtures/templates")
    zone = lib.get_template_by_name("zone")
    assert zone.parameters == {"name", "cav"}

    # create model from template
    model = Model.create(BLDG)
    bindings, hvac_zone_instance = zone.fill(BLDG)
    model.add_graph(hvac_zone_instance)

    # validate the graph (should fail because there are no labels)
    ctx = model.validate([shape_lib.get_shape_collection()])
    assert isinstance(ctx, ValidationContext)
    assert not ctx.valid
    assert len(ctx.diffset) == 1
    diff = ctx.diffset.pop()
    assert isinstance(diff.failed_shape, BNode), (
        diff.failed_shape,
        type(diff.failed_shape),
    )
    assert diff.failed_component == SH.MinCountConstraintComponent

    model.add_triples((bindings["name"], RDFS.label, Literal("hvac zone 1")))
    # validate the graph (should now be valid)
    ctx = model.validate([shape_lib.get_shape_collection()])
    assert isinstance(ctx, ValidationContext)
    assert ctx.valid


def test_model_compile(bm: BuildingMOTIF):
    """Test that model compilation gives expected results"""
    small_office_model = Model.create("http://example.org/building/")
    small_office_model.graph.parse(
        "tests/unit/fixtures/smallOffice_brick.ttl", format="ttl"
    )

    brick = Library.load(ontology_graph="libraries/brick/Brick-full.ttl")

    compiled_model = small_office_model.compile([brick.get_shape_collection()])

    precompiled_model = Graph().parse(
        "tests/unit/fixtures/smallOffice_brick_compiled.ttl", format="ttl"
    )

    assert isomorphic(compiled_model, precompiled_model)


def test_get_manifest(clean_building_motif):
    BLDG = Namespace("urn:building/")
    model = Model.create(name=BLDG)
    manifest = model.get_manifest()
    manifest.graph.add((URIRef("http://example.org/alex"), RDF.type, FOAF.Person))

    assert model.get_manifest() == manifest
    assert isomorphic(manifest.load(manifest.id).graph, manifest.graph)


def test_validate_with_manifest(clean_building_motif):
    g = Graph()
    g.parse(
        data="""
    @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
    @prefix skos: <http://www.w3.org/2004/02/skos/core#> .
    @prefix brick: <https://brickschema.org/schema/Brick#> .
    @prefix sh: <http://www.w3.org/ns/shacl#> .
    @prefix : <urn:ex/> .
    :a  a  :Class ;
        rdfs:label "a" .
    :b a :Class . # will fail
    """
    )

    manifest_g = Graph()
    manifest_g.parse(
        data="""
    @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
    @prefix skos: <http://www.w3.org/2004/02/skos/core#> .
    @prefix brick: <https://brickschema.org/schema/Brick#> .
    @prefix sh: <http://www.w3.org/ns/shacl#> .
    @prefix : <urn:ex/> .
    :shape a sh:NodeShape ;
        sh:targetClass :Class ;
        sh:property [ sh:path rdfs:label ; sh:minCount 1 ] .
    """
    )

    BLDG = Namespace("urn:building/")
    model = Model.create(name=BLDG)
    model.add_graph(g)
    manifest = model.get_manifest()
    manifest.add_graph(manifest_g)

    ctx = model.validate(None)
    assert not ctx.valid, "Model validated but it should throw an error"
