from flask import Flask, url_for, request, Response
from flask_cors import CORS, cross_origin
import json

from packaide_nester import PackaideNester

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'


def has_no_empty_params(rule):
    defaults = rule.defaults if rule.defaults is not None else ()
    arguments = rule.arguments if rule.arguments is not None else ()
    return len(defaults) >= len(arguments)


@app.route("/")
def site_map():
    links = []
    for rule in app.url_map.iter_rules():
        # Filter out rules we can't navigate to in a browser
        # and rules that require parameters
        if has_no_empty_params(rule):
            url = url_for(rule.endpoint, **(rule.defaults or {}))
            links.append((list(rule.methods), url, rule.endpoint))
    # links is now a list of url, endpoint tuples
    return links


@app.post("/nest")
@cross_origin()
def nest_post():
    format = request.args.get('format')
    content = request.json
    
    offset = float(content.get('Offset', 0.1))
    tolerance = float(content.get('Tolerance', 0.1))
    assert offset > 0.0 and tolerance > 0.0, "offset and tolerance need to be positive"

    nester = PackaideNester(offset, tolerance)

    # TODO use enum?
    if format == 'Explicit':
        sheets = [sheet['Outline'] for sheet in content['Sheets']]
        parts = content['Parts']
    elif format == 'SvgNest':
        sheets, parts, original_width, original_height = nester.parse(content['RawSvgData'])

    result = nester.nest(sheets, parts, original_width, original_height)
    return Response(result, mimetype="image/svg+xml", headers={"Content-disposition": "attachment; filename=result.svg"})


@app.post("/nestPolygons")
@cross_origin()
def nest_polygons_post():
    format = request.args.get('format')
    content = request.json

    offset = float(content.get('Offset', 0.1))
    tolerance = float(content.get('Tolerance', 0.1))
    assert offset > 0.0 and tolerance > 0.0, "offset and tolerance need to be positive"
    heuristic = int(content.get('Heuristic', 0))

    nester = PackaideNester(offset, tolerance)

    sheet_hole_polygons = content['Sheets']
    part_polygons = content['Parts']
    print(part_polygons)
    width = content['Width']
    height = content['Height']

    result = nester.nest_polygons(
        width, height, sheet_hole_polygons, part_polygons, heuristic)
    result_json = json.dumps({"transforms": result})

    return result_json


def parse_coordinate_array_from_json(string):
    return
