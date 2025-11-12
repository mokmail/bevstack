import json
from urllib.request import urlopen
from pystac import Catalog, get_stac_version , Collection , ItemCollection
from pystac.extensions.eo import EOExtension
from pystac.extensions.label import LabelExtension
import pandas as pd
import gradio as gr
import requests
from PIL import Image
from io import BytesIO
import urllib.request

import os
import json
import rasterio
import urllib.request
import pystac

from datetime import datetime, time, timezone
from shapely.geometry import Polygon, mapping
from tempfile import TemporaryDirectory
from rio_stac.stac import (
    get_dataset_geom,
    get_projection_info,
    get_raster_info,
    get_eobands_info,
    bbox_to_geom,
    get_media_type,
    create_stac_item,
)



def get_bbox_and_footprint(raster):
    with rasterio.open(raster) as r:
        bounds = r.bounds

        dataset_geom = get_dataset_geom(r, densify_pts=0, precision=5)
        projection = get_projection_info(r)
        raster_info = get_raster_info(r)
        eobands_info = get_eobands_info(r)
        media_type= get_media_type(r)
        
        bbox = dataset_geom['bbox']
        bbox_geom= bbox_to_geom(bbox)
        footprint = dataset_geom['footprint']
       

        data ={
            "bounds": bounds,
            "dataset_geom": dataset_geom,
            "projection": projection,
            "raster_info": raster_info,
            "eobands_info": eobands_info,
            "media_type": media_type,
            "bbox_geom": bbox_geom,
            "footprint": footprint
        }
        item = create_stac_item(source=r,
                                input_datetime=datetime.now(),
                                properties=data,
                                id=os.path.basename(raster).split('.')[0],
                                asset_name="image",
                                asset_media_type=media_type,
                                asset_href=raster,
                                geom_densify_pts=0,
                                geom_precision=5
                                )
        print("-----------Dataset Geom-----------")
        print(dataset_geom)
        print("----------- EOBands Info -----------")
        print(eobands_info)
        print("----------- Projection Info -----------")
        print(projection)
        print("----------- Raster Info -----------")
        print(raster_info)
        print("----------- Footprint Info -----------")
        print(dataset_geom['footprint'])
        
       


        #bbox = [bounds.left, bounds.bottom, bounds.right, bounds.top]
       
        print("----------- BBOX Info -----------")
        print(bbox_geom)

        # footprint = Polygon([
        #     [bounds.left, bounds.bottom],
        #     [bounds.left, bounds.top],
        #     [bounds.right, bounds.top],
        #     [bounds.right, bounds.bottom]
        # ])

        return (bbox, footprint , item )







def make_cataloge(images:list[str] , name="Bev Catalog") -> Catalog:
    collection_bboxes = []
    items = []
    for image in images:
        bbox, footprint, item = get_bbox_and_footprint(image)
        collection_bboxes.append(bbox)
        # itemx = pystac.Item(
        #     id=os.path.basename(image).split('.')[0],
        #     geometry=footprint,
        #     bbox=bbox,
        #     datetime=datetime.now(timezone.utc),
        #     properties={},
        #     href=image
        # )
        items.append(item)

    minx, miny, maxx, maxy = zip(*collection_bboxes)
    collection = pystac.Collection(
        id=name.replace(" ", "_").lower(),
        description="This is a collection of images from Bev",
        extent=pystac.Extent(
            spatial=pystac.SpatialExtent([min(minx), min(miny), max(maxx), max(maxy)]),
            temporal=pystac.TemporalExtent([[datetime(2020, 1, 1, tzinfo=timezone.utc), None]]),
        )

    

    )
    itemcollection = ItemCollection(items)
    for item in items:
        collection.add_item(item)

    catalog = pystac.Catalog(id="Bev_catalog",
                              description="A bev STAC catalog",
                                title="Bev Catalog",
                                href="."
                            
                              )
    catalog.add_child(collection)
    
    

    
    return collection , catalog , itemcollection
  



images = [
    'https://data.bev.gv.at/download/KM_R/KM50/20250710/KM50_UTM33N_200L_Farbtiff_mit_Relief/km50_mit_Relief_1440_2_20250710.tif',
    'https://data.bev.gv.at/download/KM_R/KM50/20250505/KM50_UTM33N_200L_Farbtiff_mit_Relief/km50_mit_Relief_1330_2_20250505.tif',
    'https://data.bev.gv.at/download/DOP/20250415/2024470_Mosaik_RGB.tif', 'https://data.bev.gv.at/download/DGM/Hoehenraster/DGM_R500.tif'
    
]
with gr.Blocks() as demo:
    
    collection, catalog , itemcollection = make_cataloge(images)

    gr.Markdown("## STAC Catalog")
    gr.Json(catalog.to_dict())
    gr.Markdown("## STAC Catalog JSON")

    
    print("----------- Item Collection -----------")
    gr.Markdown("## STAC Item Collection")
    gr.Json(itemcollection.to_dict())   

    gr.Markdown("## STAC Collection")
    gr.Json(collection.to_dict())
    with open("bev_catalog.json", "w") as f:
        content = json.dump(itemcollection.to_dict(), f, indent=4)
        #f.write(content)
        
    
        
    demo.launch()

