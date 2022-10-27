import io
import os
from pickle import TRUE
import string
import packaide
#import svgelements
import tempfile
from svgpathtools import svg2paths, wsvg, parse_path
from typing import List
import svgelements
import math
import shapely.geometry
import shapely.ops
from xml.dom import minidom
import svgwrite

# FROM PACKAIDE
# Given an svg Path element, discretize it into a polygon of points that
# are uniformly spaced the given amount of spacing apart

# Given an SVG filename, return the height and width of the viewBox
def get_sheet_dimensions(svg_string):
    doc = minidom.parseString(svg_string)
    svg = doc.getElementsByTagName('svg')[0]
    _, _, width, height = map(float, svg.getAttribute('viewBox').split())
    return height, width


def discretize_path(path, spacing):
    path = svgelements.Path(path)                  # Convert Subpath to Path
    length = path.length()
    n_points = max(3, math.ceil(length / spacing))
    points = [path.point(i * (1 / n_points)) for i in range(n_points)]
    return to_shapely_polygon(points)

# Given a sequence of svgelements Points, create a  Shapely polygon object
# represented by those points
def to_shapely_polygon(points):
    return shapely.geometry.Polygon(shapely.geometry.Point(x, y) for x, y in points)



class PackaideNester:

    def __init__(self, parts_offset, tolerance):
        self.parts_offset = parts_offset
        self.tolerance = tolerance

    def nest(self, sheets: List[str], parts_svg: str, original_width: str = '', original_height: str = ''):
        assert len(sheets) == 1, "Multiple sheets are not yet supported by nester."

        sheet = sheets[0]

        # self.validate_scaling(sheet, parts_svg)

        # Attempts to pack as many of the parts as possible.
        result, placed, fails = packaide.pack(
            [sheet],                  # A list of sheets (SVG documents)
            parts_svg,                   # An SVG document containing the parts
            tolerance=self.tolerance,          # Discretization tolerance
            offset=self.parts_offset,               # The offset distance around each shape (dilation)
            partial_solution=True,  # Whether to return a partial solution
            rotations=4,            # The number of rotations of parts to try
            persist=True            # Cache results to speed up next run
        )

        # If partial_solution was False, then either every part is placed or none
        # are. Otherwise, as many as possible are placed. placed and fails denote
        # the number of parts that could be and could not be placed respectively
        print("{} parts were placed. {} parts could not fit on the sheets".format(placed, fails))

        # The results are given by a list of pairs (i, out), where
        # i is the index of the sheet on which shapes were packed, and
        # out is an SVG representation of the parts that are to be
        # placed on that sheet.
        for i, out in result:
            with open('result_sheet_{}.svg'.format(i), 'w') as f_out:
                f_out.write(out)
        
        assert len(result) == 1, "Multiple sheets are not yet supported by nester."
        (_, svg_result) = result[0]
        
        # Create path for sheet
        sheet_paths, sheet_attributes, svg_attributes = svg2paths(
            io.StringIO(sheet), return_svg_attributes=True)
        # TODO check why packaide uses viewobx for sheet width/height
        _, _, width, height = map(float, svg_attributes['viewBox']
                                  .split())
        sheet_path = parse_path(f'M 0 0 L {width} 0 L {width} {height} L 0 {height} L 0 0 Z')
        
        # Add sheet path to nesting result svg since packaide doesn't include the sheet as path
        result_paths, result_attributes = svg2paths(io.StringIO(svg_result))
        result_paths.append(sheet_path)
        result_attributes.append(dict())
        for attribute in result_attributes:
            attribute['fill'] = 'none'
            attribute['stroke'] = 'black'
        svg_attributes['width'] = original_width if original_width != '' else svg_attributes['width']
        svg_attributes['height'] = original_height if original_height != '' else svg_attributes['height']

        # svg_attributes = {
        #     'width': f'{width}px', 
        #     'height': f'{height}px',
        #     'viewBox': f'0 0 {width} {height}'
        #     }
    
        return self.string_for_paths(result_paths, result_attributes, svg_attributes)
            

        # sheet_svg_document = svgelements.SVG.parse(io.StringIO(sheet))
        # result_svg_document = svgelements.SVG.parse(io.StringIO(svg_result))

        # return svg_result

    def parse(self, data: string):
        result_paths, result_attributes, svg_attributes = svg2paths(
            io.StringIO(data), return_svg_attributes=True)
        # TODO set viewbox of sheet element 
        sheet_path = result_paths[-1]
        (xmin, xmax, ymin, ymax) = sheet_path.bbox()
        width = xmax - xmin
        height = ymax - ymin
        sheet_svg_attributes = dict(svg_attributes)
        sheet_svg_attributes['viewBox'] = f'{xmin} {ymin} {width} {height}'
        sheet_svg_attributes['width'] = f'{width}'
        sheet_svg_attributes['height'] = f'{height}'

        # sheets = [self.string_for_paths(
            # [], [], sheet_svg_attributes)]
        sheets = []
        temp_file_path = os.path.join(
            tempfile.gettempdir(), "nesting_result.svg")
        dwg = svgwrite.Drawing(temp_file_path, size=(
            width, height), viewBox=(f'0 0 {width} {height}'))
        dwg.save()
        with open(temp_file_path) as f:
            sheets.append(f.read())
        print(sheets[0])
        
        parts_svg_attributes = dict(svg_attributes)
        xmin, ymin, width, height = map(float, svg_attributes['viewBox']
                                  .split())
        parts_svg_attributes['viewBox'] = f'{xmin} {ymin} {width} {height}'
        parts_svg_attributes['width'] = f'{width}'
        parts_svg_attributes['height'] = f'{height}'

        parts = self.string_for_paths(
            result_paths[:-2], result_attributes[:-2], parts_svg_attributes)

        return sheets, parts, svg_attributes['width'], svg_attributes['height']

    def string_for_paths(self, paths, path_attributes, svg_attributes={}):
        # TODO skip write/load cycle by using in memory stream
        temp_file_path = os.path.join(
            tempfile.gettempdir(), "nesting_result.svg")
        wsvg(paths, attributes=path_attributes,
             svg_attributes=svg_attributes, filename=temp_file_path)

        with open(temp_file_path) as f:
            joined_result_svg = f.read()
            return joined_result_svg

    def validate_scaling(self, sheet, parts):
        height, width = get_sheet_dimensions(sheet)
        print(f'sheet dimensions: {width}x{height}')

        svg_object = svgelements.SVG.parse(
            io.StringIO(parts), width=width, height=height)
        print(f'parts bounding boxes:')
        for element in svg_object.elements():
            if isinstance(element, svgelements.Path):
                poly = discretize_path(element.subpath(0), 0.1).simplify(0.1)
                print(poly.bounds)

