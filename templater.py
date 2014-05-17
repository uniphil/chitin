#!/usr/bin/env python
import os
import json
import jinja2
from jinja2 import nodes
from jinja2.ext import Extension
from jinja2.parser import describe_token

SITE_DIR = 'site'
CONTENT_DIR = 'content'
OUTPUT_DIR = 'output'


iterdata_hack = {}


class LoadContentExtension(Extension):
    tags = set(['load'])

    def parse(self, parser):
        """Parse an assign statement."""
        lineno = next(parser.stream).lineno
        token = parser.stream.current
        if token.type == 'name':
            print('got an name', token.value)
            name = token.value
            next(parser.stream)
            data = load_by_name(name)
        elif token.type == 'string':
            print('got a string', token.value)
            if not token.value.startswith('%'):
                parser.fail('expected a string starting with %')
            iter_name = token.value[1:]
            data = iterdata_hack[iter_name]
            next(parser.stream)
            parser.stream.expect('name:as')
            name = parser.parse_assign_target().name
        else:
            parser.fail('expected a name or string, not {}.'.format(describe_token(token)), token.lineno)
        return nodes.Assign(nodes.Name(name, 'store', lineno=token.lineno), nodes.Const(data), lineno=lineno)


env = jinja2.Environment(undefined=jinja2.StrictUndefined,
                         loader=jinja2.FileSystemLoader(SITE_DIR),
                         extensions=[LoadContentExtension])


def load_by_name(name):
    print('loading {}'.format(name))
    filepath = os.path.join(CONTENT_DIR, '{}.json'.format(name))
    with open(filepath) as file_obj:
        data = json.load(file_obj)
    return data


def load_iterdata_by_name(name):
    return load_by_name(name)


def walk_site(dir=None, out_path=None, path_ctx=None):
    dir = dir or SITE_DIR
    out_path = out_path or ''
    path_ctx = path_ctx or {}

    for item in os.listdir(dir):
        if item.startswith('_'):
            continue
        template_path = os.path.join(dir, item)
        if os.path.isdir(template_path):
            if item.startswith('%'):
                name, prop = item[1:].split('.', 1)
                if name in path_ctx:
                    path_var = path_ctx[name][prop]
                    out_path = '{}/{}'.format(dir, path_var)
                    for thing in walk_site(template_path, out_path, path_ctx):
                        yield thing
                else:
                    data = load_by_name(name)
                    for thing in data:
                        path_ctx[name] = thing
                        path_var = thing[prop]
                        out_path = '{}/{}'.format(dir, path_var)
                        for thing in walk_site(template_path, out_path, path_ctx):
                            yield thing
                    del path_ctx[name]
                print(name, prop)
            else:
                out_path = '{}/{}'.format(dir, item)
                for thing in walk_site(template_path, out_path, path_ctx):
                    yield thing
        else:
            out_filepath = '{}/{}'.format(out_path, item)
            yield template_path, out_filepath, path_ctx


def render_site():
    for template_path, output_path, iterdata_ctx in walk_site():
        global iterdata_hack
        iterdata_hack = iterdata_ctx
        print '||||||||||||||||||||| RENDRING {} |||||||||||||||||'.format(template_path)
        template = env.get_template(template_path[len(SITE_DIR)+1:])
        print template.render()

render_site()

#template = env.get_template('index.html')
#print template.render()

