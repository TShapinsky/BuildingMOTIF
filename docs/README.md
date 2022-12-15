# BuildingMOTIF

[![codecov](https://codecov.io/gh/NREL/BuildingMOTIF/branch/main/graph/badge.svg?token=HAFSYH45NX)](https://codecov.io/gh/NREL/BuildingMOTIF) 
[![Jupyter Book Badge](https://jupyterbook.org/badge.svg)](https://nrel.github.io/BuildingMOTIF/)

> *Enabling the enabling technology of semantic interoperability.*

Semantic Interoperability in buildings through standardized semantic metadata is crucial to unlocking the value of the abundant and diverse networked data in buildings, avoiding subsequent data incompatibility/interoperability issues, and paving the way for advanced building technologies like Automated Fault Detection and Diagnostics (AFDD), real-time energy optimization, other energy management information systems ([EMIS](https://www.energy.gov/eere/femp/what-are-energy-management-information-systems)), improved HVAC controls, and grid-interactive energy efficient building ([GEB](https://www.energy.gov/eere/buildings/grid-interactive-efficient-buildings)) technologies, all of which are needed to fully de-carbonize buildings. Utilizing the capabilities of [Semantic Web](https://www.w3.org/standards/semanticweb/), it is possible to standardize building metadata in structured, expressive, and machine-readable ways, but at the same time it is very important to make it easier to implement for field practitioners without advanced knowledge in computer science. 

***Building Metadata OnTology Interoperability Framework (BuildingMOTIF)*** bridges that gap between theory and practice, by offering a toolset for building metadata creation, storage, visualization, and validation. It is offered in the form of an SDK with easy-to-use APIs that abstract the underlying complexities of [RDF](https://www.w3.org/RDF/) graphs, database management, [SHACL](https://www.w3.org/TR/shacl/) validation, and interoperability between different metadata schemas/ontologies. It also supports connectors for easier integration with existing metadata sources (e.g., Building Automation System data, design models, existing metadata models, etc.), which are available at different phases of the building life-cycle.

The objectives of the ***BuildingMOTIF*** toolset are the following:
1. lower costs, reduce installation time, and improve delivered quality of building controls and services for building owners and occupants
2. enable a simpler and more easily verifiable procurement process for products and services for building managers
3. open new business opportunities for service providers, by removing knowledge barriers for parties implementing building controls and services

Currently, ***BuildingMOTIF*** is planned to support the [Brick Schema](https://brickschema.org/), [Project Haystack](https://project-haystack.org/), and the proposed [ASHRAE Standard 223P](https://www.ashrae.org/about/news/2018/ashrae-s-bacnet-committee-project-haystack-and-brick-schema-collaborating-to-provide-unified-data-semantic-modeling-solution), and to offer both a UI and underlying SDK with tutorials and reference documentation to be useful for different levels of expertise of users for maximum adoption.

# Documentation

The documentation uses [Diataxis](https://diataxis.fr/) as a framework for its structure, which is organized into the following sections.

## Tutorials

- [Model Creation](https://nrel.github.io/BuildingMOTIF/tutorials/model_creation.html)
- [Model Validation](https://nrel.github.io/BuildingMOTIF/tutorials/model_validation.html)
- [Model Correction](https://nrel.github.io/BuildingMOTIF/tutorials/model_correction.html)
- [Template Writing](https://nrel.github.io/BuildingMOTIF/tutorials/template_writing.html)

## How-to Guides

🏗️ under construction

## Reference

- [Code Documentation](https://nrel.github.io/BuildingMOTIF/reference/apidoc/index.html)
- [Developer Documentation](https://nrel.github.io/BuildingMOTIF/reference/developer_documentation.html)

## Explanation

🏗️ under construction