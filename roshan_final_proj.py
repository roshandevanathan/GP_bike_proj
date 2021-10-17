#Roshan Devanathan, Final Proj
import os
import processing 
from qgis.core import QgsVectorLayer, QgsRasterLayer, QgsProject
from PyQt5.QtCore import QVariant
from PyQt5.QtGui import *

# Set path to folder
loc = "H:/GP_bike_proj/"

#Add Base Layers to Map
Bicycle_Network = QgsVectorLayer(loc+"Bicycle_Network/Bicycle_Network.json", "Bicycle_Network", "ogr")
if not Bicycle_Network.isValid():
    print("Layer failed to load!")
else:
    QgsProject.instance().addMapLayer(Bicycle_Network)
    
Traffic_Volume = QgsVectorLayer(loc+"Traffic_Volume/Traffic_Volume.shp", "Traffic_Volume", "ogr")
if not Traffic_Volume.isValid():
    print("Layer failed to load!")
else:
    QgsProject.instance().addMapLayer(Traffic_Volume)

speed_zones_clipped = QgsVectorLayer(loc+"speed_zones_clipped.shp", "speed_zones_clipped", "ogr")
if not speed_zones_clipped.isValid():
    print("Layer failed to load!")
else:
    QgsProject.instance().addMapLayer(speed_zones_clipped)
    
EXTRACT_POLYGON = QgsVectorLayer(loc+"EXTRACT_POLYGON.shp", "EXTRACT_POLYGON", "ogr")
if not EXTRACT_POLYGON.isValid():
    print("Layer failed to load!")
else:
    QgsProject.instance().addMapLayer(EXTRACT_POLYGON)
    
#Run vector tool operations
#clip traffic
processing.runAndLoadResults("native:clip", {'INPUT':'H:/GP_bike_proj/Traffic_Volume (1)/Traffic_Volume.shp','OVERLAY':'H:/GP_bike_proj/Order_D19UD5/ll_gda2020/esrishape/user_polygon/user_polygon-0/EXTRACT_POLYGON.shp','OUTPUT':'H:/GP_bike_proj/Traffic_Clipped.shp'})
#Create Buffers for all
processing.runAndLoadResults("native:buffer", {'INPUT':'H:/GP_bike_proj/Traffic_Clipped.shp|layername=Traffic_Clipped','DISTANCE':7,'SEGMENTS':5,'END_CAP_STYLE':0,'JOIN_STYLE':0,'MITER_LIMIT':2,'DISSOLVE':False,'OUTPUT':'H:/GP_bike_proj/Traffic_clipped_buffer.shp'})
processing.runAndLoadResults("native:buffer", {'INPUT':'H:/GP_bike_proj/Bicycle_Network/Bicycle_Network.json|layername=Bicycle_Network','DISTANCE':0.0001,'SEGMENTS':5,'END_CAP_STYLE':0,'JOIN_STYLE':0,'MITER_LIMIT':2,'DISSOLVE':False,'OUTPUT':'H:/GP_bike_proj/Bike_network_buffer.shp'})
processing.runAndLoadResults("native:buffer", {'INPUT':'H:/GP_bike_proj/speed_zones_clipped.shp','DISTANCE':7,'SEGMENTS':5,'END_CAP_STYLE':0,'JOIN_STYLE':0,'MITER_LIMIT':2,'DISSOLVE':False,'OUTPUT':'H:/GP_bike_proj/speed_clipped_buffer.shp'})
#Union all 3 buffers
processing.run("native:union", {'INPUT':'H:/GP_bike_proj/Traffic_clipped_buffer.shp','OVERLAY':'H:/GP_bike_proj/Bike_network_buffer.shp','OUTPUT':'H:/GP_bike_proj/union_bike_traffic.shp'})
processing.runAndLoadResults("native:union", {'INPUT':'H:/GP_bike_proj/speed_clipped_buffer.shp','OVERLAY':'H:/GP_bike_proj/union_bike_traffic.shp.shp','OUTPUT':'H:/GP_bike_proj/union_final.shp'})
#Clean up file
union_final = QgsVectorLayer(loc+"union_final.shp", "union_final.shp", "ogr")
with edit(union_final):
    processing.run("qgis:selectbyexpression", {'INPUT':'H:/GP_bike_proj/Bike_network_buffer.shp','EXPRESSION':'Descriptio=\'Local Road\' or \r\nDescriptio=\'Shared Path\' or\r\nDescriptio = \'Walking Track\'\r\nor\r\n(Descriptio is not null and\r\nSIGN_SPEED is not null and\r\nALLVEHS_AA is not null)\r\n','METHOD':0})
    union_final.invertSelection()
    union_final.deleteSelectedFeatures()
#Create Rank field 
layer_provider=union_final.dataProvider()
layer_provider.addAttributes([QgsField("Rank",QVariant.String)])
union_final.updateFields()
#Calculate Rank
features=union_final.getFeatures()
union_final.startEditing()
for feature in features:
    id=feature.id()
    if(feature["Descriptio"] == "Walking Track"):
        feature["Rank"] = "low"
    if(feature["Descriptio"] == "Shared Path"):
        feature["Rank"] = "low"
    if(feature["Descriptio"] == "Interesection"):
        feature["Rank"] = "high"
        
    if(feature["Descriptio"] ==  "Local Road" or feature["Descriptio"] == "Standard bicycle lane"): 
        if(feature["SIGN_SPEED"] >= 30):
            feature["Rank"] = "medium"
        if(feature["ALLVEHS_AA"] >= 3000):
            feature["Rank"] = "medium"
        else:
            feature["Rank"] = "low"
    
    if(feature["Descriptio"] ==  "Arterial  Road" or feature["Descriptio"] == "Sub-Arterial Road" or feature["Descriptio"] == "Collector Road"): 
        if(feature["SIGN_SPEED"] >= 55):
            feature["Rank"] = "high"
        if(feature["ALLVEHS_AA"] >= 5000):
            feature["Rank"] = "high"
        else:
            feature["Rank"] = "medium"        
    
    if(feature["Descriptio"] ==  "Traffic protecting chevron" or feature["Descriptio"] == "Total protecte chevron (protect from dooring and *" or feature["Descriptio"] ==  "dooring protecting chevron" or feature["Descriptio"] ==  "Kerb side physically separated"):         
        feature["Rank"]="medium"
    
    union_final.updateFeature(feature)
union_final.commitChanges()