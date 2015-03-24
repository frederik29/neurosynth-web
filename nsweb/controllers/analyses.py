from flask import (Blueprint, render_template, redirect, url_for, request,
                   jsonify, abort)
from nsweb.models.analyses import (Analysis, AnalysisSet, TopicAnalysis,
                                   TermAnalysis)
from nsweb.core import add_blueprint
from nsweb.controllers import images
import json
import re

bp = Blueprint('analyses', __name__, url_prefix='/analyses')


### ROUTES COMMON TO ALL ANALYSES ###
def find_analysis(name, type=None):
    ''' Retrieve analysis by either id (when int) or name (when string) '''
    if re.match('\d+$', name):
        return Analysis.query.get(name)
    return Analysis.query.filter_by(type=type, name=name).first()


@bp.route('/<string:val>/images')
def get_images(val):
    analysis = find_analysis(val)
    images = [{
        'id': img.id,
        'name': img.label,
        'colorPalette': 'red' if 'reverse' in img.label else 'blue',
        # "intent": (img.stat + ':').capitalize(),
        'url': '/images/%s' % img.id,
        'visible': 1 if 'reverse' in img.label else 0,
        'download': '/images/%s' % img.id,
        'intent': 'z-score'
    } for img in analysis.images if img.display]
    return jsonify(data=images)


@bp.route('/<string:type>/<string:name>/images/<string:image>/')
@bp.route('/topics/<string:topic_set>/<string:name>/images/<string:image>/')
def get_image(name, image, type=None, topic_set=None):
    if type is None:
        analysis = TopicAnalysis.query.join(AnalysisSet).filter(
            TopicAnalysis.number == int(name),
            AnalysisSet.name == topic_set).first()
    else:
        type = {'topics': 'topic', 'terms': 'term', 'custom': 'custom'}[type]
        analysis = find_analysis(name, type=type)
    unthresholded = ('unthresholded' in request.args.keys())
    if re.match('\d+$', image):
        img = analysis.images[int(image)]
    elif image in ['reverse', 'forward']:
        img = [i for i in analysis.images if image in i.label][0]
    return images.download(img.id, unthresholded)


@bp.route('/<string:val>/studies')
def get_studies(val):
    analysis = find_analysis(val)
    if 'dt' in request.args:
        data = []
        for f in analysis.frequencies:
            s = f.study
            link = '<a href={0}>{1}</a>'.format(
                url_for('studies.show', val=s.pmid), s.title)
            data.append([link, s.authors, s.journal, round(f.frequency, 3)])
        data = jsonify(data=data)
    else:
        data = jsonify(studies=[s.pmid for s in analysis.studies])
    return data


### TOP INDEX ###
@bp.route('/')
def list_analyses():
    n_terms = TermAnalysis.query.count()
    return render_template('analyses/index.html.slim', n_terms=n_terms)


### TERM-SPECIFIC ROUTES ###
@bp.route('/term_names/')
def get_term_names():
    # optimize this later--select only names
    names = [f.name for f in TermAnalysis.query.all()]
    return jsonify(data=names)


@bp.route('/terms/')
def list_terms():
    return render_template('analyses/terms/index.html.slim')


@bp.route('/terms/<string:term>/')
def show_term(term):
    analysis = find_analysis(term, type='term')
    if analysis is None:
        return render_template('analyses/missing.html.slim', analysis=term)
    return render_template('analyses/terms/show.html.slim',
                           analysis=analysis,
                           cog_atlas=json.loads(analysis.cog_atlas or '{}'))


### TOPIC-SPECIFIC ROUTES ###
@bp.route('/topics/')
def list_topic_sets():
    topic_sets = AnalysisSet.query.filter_by(type='topics')
    return render_template('analyses/topics/index.html.slim',
                           topic_sets=topic_sets)


@bp.route('/topics/<string:topic_set>/')
def show_topic_set(topic_set):
    topic_set = AnalysisSet.query.filter_by(name=topic_set).first()
    return render_template('analyses/topics/show_set.html.slim',
                           topic_set=topic_set)


@bp.route('/topics/<string:topic_set>/<string:number>')
def show_topic(topic_set, number):
    topic = TopicAnalysis.query.join(AnalysisSet).filter(
        TopicAnalysis.number == number, AnalysisSet.name == topic_set).first()
    if topic is None:
        return render_template('analyses/missing.html.slim', analysis=None)
    terms = [t[0] for t in TermAnalysis.query.with_entities(
        TermAnalysis.name).all()]
    top = topic.terms.split(', ')

    def map_url(x):
        if x in terms:
            return '<a href="%s">%s</a>' % (url_for('analyses.show_term',
                                                    term=x), x)
        return x
    topic.terms = ', '.join(map(map_url, top))
    return render_template('analyses/topics/show.html.slim',
                           analysis_set=topic.analysis_set, analysis=topic)


### FALLBACK GENERIC ROUTE ###
@bp.route('/<string:id>/')
def show_analysis(id):
    analysis = find_analysis(id)
    if analysis is None:
        return render_template('analyses/missing.html.slim', analysis=id)
    if analysis.type == 'term':
        return redirect(url_for('analyses.show_term', term=analysis.name))
    elif analysis.type == 'topic':
        return redirect(url_for('analyses.show_topic', number=analysis.number,
                                topic_set=analysis.analysis_set.name))

add_blueprint(bp)
