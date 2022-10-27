from flask import Flask, url_for, request, Response
from flask_cors import CORS, cross_origin

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
    nester = PackaideNester(offset)

    # TODO use enum?
    if format == 'Explicit':
        sheets = [sheet['Outline'] for sheet in content['Sheets']]
        parts = content['Parts']
    elif format == 'SvgNest':
        sheets, parts, original_width, original_height = nester.parse(content['RawSvgData'])

    result = nester.nest(sheets, parts, original_width, original_height)



    
    return Response(result, mimetype="image/svg+xml", headers={"Content-disposition": "attachment; filename=result.svg"})
