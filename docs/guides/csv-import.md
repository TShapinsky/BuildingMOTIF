# CSV Import

Assume we have the following CSV file:

```
name,room,name-co2,name-temp,name-sp
tstat2,room345,co2-345,temp-345,sp-345
tstat3,room567,cow-567,temp-567,sp-567
```

And the following Template in a library called `csv-tutorial`:

```yml
my-thermostat:
  body: >
    @prefix P: <urn:___param___#> .
    @prefix brick: <https://brickschema.org/schema/Brick#> .
    P:name a brick:Thermostat ;
        brick:hasLocation P:room .
  dependencies:
  - template: https://brickschema.org/schema/Brick#Room
    library: https://brickschema.org/schema/1.3/Brick
    args: {"name": "room"}
  - template: my-tstat-points
    args: {"name": "name"}
    
my-tstat-points:
  body: >
    @prefix P: <urn:___param___#> .
    @prefix brick: <https://brickschema.org/schema/Brick#> .
    P:name a brick:Thermostat ;
        brick:hasPoint P:temp, P:sp, P:co2 .
  dependencies:
    - template: https://brickschema.org/schema/Brick#Temperature_Sensor
      library: https://brickschema.org/schema/1.3/Brick
      args: {"name": "temp"}
    - template: https://brickschema.org/schema/Brick#Temperature_Setpoint
      library: https://brickschema.org/schema/1.3/Brick
      args: {"name": "sp"}
    - template: https://brickschema.org/schema/Brick#CO2_Sensor
      library: https://brickschema.org/schema/1.3/Brick
      args: {"name": "co2"}
```

We can create a CSV ingress handler using the built-in class ([`CSVIngressHandler`](/reference/apidoc/_autosummary/buildingmotif.ingresses.csv.html#buildingmotif.ingresses.csv.CSVIngress)):

```python
from rdflib import Namespace, Graph
from buildingmotif import BuildingMOTIF
from buildingmotif.namespaces import BRICK
from buildingmotif.dataclasses import Model, Library, Template
from buildingmotif.ingresses import CSVIngress, TemplateIngress, Record

bm = BuildingMOTIF("sqlite://") # in-memory
BLDG = Namespace("urn:my_site/")
model = Model.create(BLDG) # create our model
lib = Library.load(directory="csv-tutorial") # load in the library containing our template

csv = CSVIngress("data.csv") # the CSV file above
ingress = TemplateIngress(tstat_templ.inline_dependencies(), None, csv)
graph = ingress.graph(BLDG)
print(graph.serialize()) # print the resulting model
```

The `None` on the final line of the cell above is the "mapper".
