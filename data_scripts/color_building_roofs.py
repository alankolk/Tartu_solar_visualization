# https://pythonhosted.org/pykml/examples/kml_reference_examples.html
# https://stackoverflow.com/questions/51789543/write-kml-file-from-another

from pykml import parser
from lxml import etree 
from pykml.factory import KML_ElementMaker as KML

from pyproj import Transformer

import json

def read_tile_json(filepath):
    f = open(filepath)
    data = json.load(f)

    tile_list = []

    for line in data:
        tile = data[line]["tile"]
        if len(tile_list) != 0 and tile_list[-1] == tile:
            continue
        tile_list.append(tile)
    
    f.close()
    return tile_list

def transform_roof_coordinates(coordinates, transformer):

    coordinate_list = []

    for coord in coordinates:
        transformed = transformer.transform(coord[0], coord[1])

        coordinate_list.append([round(transformed[1], 7), round(transformed[0], 7), round(coord[2], 2)])
    
    return coordinate_list

def modify_buildings_in_tiles(filepath, tiles, roof_attr_path):
    
    roof_attr_data = open(roof_attr_path)
    roof_data = json.load(roof_attr_data)

    transformer = Transformer.from_crs("epsg:3301", "epsg:4326")

    for tile in tiles:
        with open(filepath + str(tile[0]) + "/" + str(tile[1]) + "/" + "Tartu_Tile_" + str(tile[0]) + "_" + str(tile[1]) + "_geometry.kml") as f:
            doc = parser.parse(f)

            remove_list = []

            for elem in doc.getroot().Document.Placemark:
                if "RoofSurface" in elem.name.text:
                    polygons = elem.MultiGeometry.getchildren()
                    remove_list.append([elem, polygons])

            for tuple in remove_list:
                element = tuple[0]

                element_name = element.name.text
                element_id = element_name[5:element_name.index("_", 5)] #Only extract etak id number from the name, format is "etak_######_..."

                try: #Atleast one building exists in the KML visual export that is not present in the cityGML file that was created by the estonian landboard, so this try block goes past this anomaly
                    polygons_from_roof_data = roof_data[element_id]["roofs"]
                except:
                    continue

                for poly in tuple[1]:
                    #TODO Create colour based on the potential of the side
                    #For this find the range of the yearly_kwh and then map colours based on the values

                    coords = []
                    for coord in poly.outerBoundaryIs.LinearRing.coordinates.text.split(" "):
                        if len(coords) == 3:
                            break
                        float_coord = []
                        for convert in coord.split(","):
                            float_coord.append(float(convert))
                        if len(coords) != 0 and coords[-1] == float_coord:
                            continue
                        else:
                            coords.append(float_coord)
                    
                    roof_coords = []
                    roof_orientation = ""
                    roof_potential = ""

                    for roof_polygon in polygons_from_roof_data:
                        roof_coords = transform_roof_coordinates(roof_polygon["points_epsg_3301"], transformer)

                        if (coords[0] in roof_coords and coords[1] in roof_coords and coords[2] in roof_coords): #We have a match with the coords from the kml polygon and the city-attributes roof coordinates
                            #IF MATCH, then we want the potential yearly_kwh data and the orientatation?
                            #roof_potential = roof_polygon["yearly_kwh"]
                            roof_orientation = roof_polygon["orientation"]

                    colour = "FF000000" #Default must

                    match roof_orientation:
                        case "none":
                            colour = "FF5A32EB" #Lillakassinine
                        case "south":
                            colour = "FFFFB140" #Oranz
                        case "east":
                            colour = "FFBB2B60" #Roosakaspunane
                        case "west":
                            colour = "FF679C34" #Roheline
                        case "north":
                            colour = "FF55D3FC" #Helesinine
                            
                    pm = KML.Placemark(
                        KML.name(element.name.text),
                        KML.Style(
                            KML.PolyStyle(
                                KML.color(colour)
                            )
                        ),
                        poly,
                        id = element.name.text
                    )

                    doc.getroot().Document.append(pm)

                doc.getroot().Document.remove(element) #Remove the original roofsurface placemark
    
        with open(filepath + str(tile[0]) + "/" + str(tile[1]) + "/" + "Tartu_Tile_" + str(tile[0]) + "_" + str(tile[1]) + "_geometry.kml", "wb") as output:
            output.write(etree.tostring(doc,pretty_print=True))
    roof_attr_data.close()


modify_buildings_in_tiles(
                          "3dwebclient/cities/tartu2/Tiles/",
                          read_tile_json("3dwebclient/cities/tartu2/Tartu.json"),
                          "data/city-attributes.json"
                         )
