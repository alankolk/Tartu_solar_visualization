import json
import csv
import pandas as pd

def describe_yearly_kwh():
    roof_attr_data = open("data/city-attributes.json")
    roof_data = json.load(roof_attr_data)

    all_yearly_kwh = []
    for element in roof_data:
        try: #Atleast one building exists in the KML visual export that is not present in the cityGML file that was created by the estonian landboard, so this try block goes past this
            polygons_from_roof_data = roof_data[element]["roofs"]
        except:
            continue
        
        for roof_polygon in polygons_from_roof_data:
            all_yearly_kwh.append(roof_polygon["yearly_kwh"])
    
    df = pd.DataFrame(all_yearly_kwh)
    print(df.describe(percentiles=[.01,.05,.10,.25,.35,.5,.65,.75,.85,.95,.99,.999]).apply(lambda s: s.apply('{0:.5f}'.format)))
    roof_attr_data.close()

def generate_csv():
    roof_attr_data = open("data/city-attributes.json")
    roof_data = json.load(roof_attr_data)

    all_yearly_kwh = []


    with open("3dwebclient/cities/tartu2/metadata.csv", encoding="utf-8") as csv_file:
        with open("3dwebclient/cities/tartu2/metadata_new.csv", "w", newline="", encoding="utf-8") as new_file:
            metadata = csv.reader(csv_file, delimiter=",")

            writer = csv.writer(new_file, delimiter=",")

            line_count = 0

            for row in metadata:
                if line_count == 0:
                    new_columns = row + ["area","yearly_kwh","monthly_average_kwh","monthly_kwh"]
                    writer.writerow(new_columns)
                    line_count += 1
                else:#Process row
                    element_id = row[0][5:row[0].index("_", 5)]
                    try: #Atleast one building exists in the KML visual export that is not present in the cityGML file that was created by the estonian landboard, so this try block goes past this
                        polygons_from_roof_data = roof_data[element_id]["roofs"]
                        
                        area = 0.0
                        yearly_kwh = 0.0
                        monthly_average_kwh = 0.0
                        monthly_kwh = [0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0]
                        
                        for roof_polygon in polygons_from_roof_data:
                            yearly_kwh_data = roof_polygon["yearly_kwh"]
                            yearly_kwh += yearly_kwh_data
                            all_yearly_kwh.append(yearly_kwh_data)
                            area += roof_polygon["area"]
                            monthly_average_kwh += roof_polygon["monthly_average_kwh"]
                            for index, month in enumerate(roof_polygon["monthly_kwh"]):
                                monthly_kwh[index] += month
                        
                        for index, month in enumerate(monthly_kwh):
                            monthly_kwh[index] = round(month, 2)

                        row[0] = row[0] + "_RoofSurface"
                        new_row = row + [round(area, 2), round(yearly_kwh, 2), round(monthly_average_kwh, 2), str(monthly_kwh)]
                        writer.writerow(new_row)
                    except:
                        row[0] = row[0] + "_RoofSurface"
                        new_row = row + [round(area, 2), round(yearly_kwh, 2), round(monthly_average_kwh, 2), str(monthly_kwh)]
                        writer.writerow(new_row)

#describe_yearly_kwh()
#generate_csv()
    

