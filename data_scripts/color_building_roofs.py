# https://pythonhosted.org/pykml/examples/kml_reference_examples.html
# https://stackoverflow.com/questions/51789543/write-kml-file-from-another

from pykml import parser
from lxml import etree 
from pykml.factory import KML_ElementMaker as KML

from pyproj import Transformer

import json

#Reads the metadata JSON file, which contains info on what tile each building is

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

#Transforms the roof coordinates from city-attributes.json to WGS:84

def transform_roof_coordinates(coordinates, transformer):

    coordinate_list = []

    for coord in coordinates:
        transformed = transformer.transform(coord[0], coord[1])

        coordinate_list.append([round(transformed[1], 7), round(transformed[0], 7), round(coord[2], 2)])
    
    return coordinate_list

#Function to pick a colour based on the solar potential

def pick_colour(kwh):
    colour = "FFFFFFFF"
    if kwh < 450:
        colour = "#FF18FF00"
    elif kwh >= 450 and kwh < 680:
        colour = "FF00FA57"
    elif kwh >= 680 and kwh < 1000:
        colour = "FF00F38B"
    elif kwh >= 1000 and kwh < 2100:
        colour = "FF00EABC"
    elif kwh >= 2100 and kwh < 3000:
        colour = "FF00E0EB"
    elif kwh >= 3000 and kwh < 4800:
        colour = "FF00D5FF"
    elif kwh >= 4800 and kwh < 7100:
        colour = "FF00C9FF"
    elif kwh >= 7100 and kwh < 9800:
        colour = "FF00BBFF"
    elif kwh >= 9800 and kwh < 14500:
        colour = "FF00AAFF"
    elif kwh >= 14500 and kwh < 37200:
        colour = "FF0095FF"
    elif kwh >= 37200 and kwh < 124600:
        colour = "FF007BFF"
    elif kwh >= 124600 and kwh < 366000:
        colour = "FF0056FF"
    elif kwh >= 366000:
        colour = "FF9600FF"
    return colour

#Function to create a placemark with a polygon coloured a specific colour

def create_placemark(name, colour, polygon):
    pm = KML.Placemark(
        KML.name(name),
        KML.Style(
            KML.PolyStyle(
                KML.color(colour)
            )
        ),
        polygon,
        id = name
    )
    return pm

# Main function that takes the KML visualization export, tile list and city-attributes.json from the pipeline

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

                try: #Atleast one building exists in the KML visual export that is not present in the cityGML file that was created by the estonian landboard, so this try block goes past this and leaves the building untouched
                    polygons_from_roof_data = roof_data[element_id]["roofs"]
                except:
                    continue

                for poly in tuple[1]:

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

                    roof_potential = 0

                    for roof_polygon in polygons_from_roof_data:
                        roof_coords = transform_roof_coordinates(roof_polygon["points_epsg_3301"], transformer)

                        if (coords[0] in roof_coords and coords[1] in roof_coords and coords[2] in roof_coords): #WMatch the coords from the kml polygon and the city-attributes roof coordinates
                            #IF MATCH, then we want to find the potential yearly_kwh data
                            roof_potential = roof_polygon["yearly_kwh"]

                    colour = "FFFFFFFF" #Default white
   
                    if roof_potential != 0:
                        colour = pick_colour(roof_potential)

                    pm = create_placemark(element_name, colour, poly)
                            
                    doc.getroot().Document.append(pm) # Add new single polygon placemark

                doc.getroot().Document.remove(element) #Remove the original roofsurface placemark
    
        with open(filepath + str(tile[0]) + "/" + str(tile[1]) + "/" + "Tartu_Tile_" + str(tile[0]) + "_" + str(tile[1]) + "_geometry.kml", "wb") as output:
            output.write(etree.tostring(doc,pretty_print=True))
    roof_attr_data.close()


modify_buildings_in_tiles(
                          "3dwebclient/cities/tartu2/Tiles/",
                          read_tile_json("3dwebclient/cities/tartu2/Tartu.json"),
                          "data/city-attributes.json"
                         )
