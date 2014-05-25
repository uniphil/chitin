#!/usr/bin/env python
from __future__ import print_function

import os
import json
import shutil
import jinja2
from jinja2 import nodes
from jinja2.ext import Extension
from jinja2.parser import describe_token


SITE_DIR = 'site'
CONTENT_DIR = 'data'
OUTPUT_DIR = 'build'

SKIP_PREFIX = '_'
LOAD_PREFIX = '%'
COPY_PREFIX = 'b%'


class LoadContentExtension(Extension):
    tags = set(['load'])

    def __init__(self, environment):
        super(LoadContentExtension, self).__init__(environment)
        environment.extend(load_content_context={})

    def parse(self, parser):
        """Parse an assign statement."""
        lineno = next(parser.stream).lineno
        token = parser.stream.current
        if token.type != 'string':
            parser.fail('expected a string, not {}.'
                        .format(describe_token(token)), token.lineno)
        if token.value.startswith(LOAD_PREFIX):
            context_name = token.value[len(LOAD_PREFIX):]
            data = self.environment.load_content_context[context_name]
        else:
            data = load_data(token.value)
        next(parser.stream)
        parser.stream.expect('name:as')
        name = parser.parse_assign_target().name

        return nodes.Assign(nodes.Name(name, 'store', lineno=token.lineno),
                            nodes.Const(data), lineno=lineno)


env = jinja2.Environment(undefined=jinja2.StrictUndefined,
                         loader=jinja2.FileSystemLoader(SITE_DIR),
                         extensions=[LoadContentExtension])


env.load_content_data_dir = CONTENT_DIR


def load_data(name):
    filepath = os.path.join(CONTENT_DIR, '{}.json'.format(name))
    with open(filepath) as file_obj:
        data = json.load(file_obj)
    return data


def copydata(name, output_dir):
    src_path = os.path.join(CONTENT_DIR, name)
    filename = os.path.split(name)[1]
    dest_path = os.path.join(OUTPUT_DIR, output_dir, filename)
    try:
        print('trying to copy from', src_path)
        shutil.copy(src_path, dest_path)
    except IOError as e:
        if os.path.isdir(src_path):
            shutil.copytree(src_path, dest_path)
        else:
            raise e


def writedata(output_path, content):
    rel_path = os.path.join(OUTPUT_DIR, output_path)
    with open(rel_path, 'w') as output_file:
        output_file.write(content)


def link(path):
    return '/{}'.format(path)


def walk_site(site_directory='', context=None, output_path=''):
    context = context or {}  # do not mutate this yo.

    # create the output path folder
    try:
        os.makedirs(os.path.join(OUTPUT_DIR, output_path))
    except:
        print('folder already exists in out??? output/{}'.format(output_path))

    relpath = os.path.join(SITE_DIR, site_directory)
    filenames = set(os.listdir(relpath))
    skipables = set(filter(lambda n: n.startswith(SKIP_PREFIX), filenames))
    copyables = set(filter(lambda n: n.startswith(COPY_PREFIX), filenames))
    loadables = set(filter(lambda n: n.startswith(LOAD_PREFIX), filenames))
    recurseables = set(filter(lambda name:
        os.path.isdir(os.path.join(relpath, name)), filenames))
    recurseables = recurseables - copyables - loadables
    templateables = filenames - loadables - copyables - skipables - recurseables

    # copy stuff
    for prefixed_name in copyables:
        name = prefixed_name[len(COPY_PREFIX):]
        copydata(name, output_path)

    # render stuff
    for template_name in templateables:
        env.load_content_context = context
        template_sitepath = os.path.join(site_directory, template_name)
        template = env.get_template(template_sitepath)
        rendered = template.render(link=link)
        output_template_path = os.path.join(output_path, template_name)
        writedata(output_template_path, rendered)

    # easymode recurse
    for name in recurseables:
        sub_context = context.copy()  # defensive; unnecessary
        sub_dir = os.path.join(site_directory, name)
        sub_path = '{}/{}'.format(output_path, name) if output_path else name
        walk_site(sub_dir, sub_context, sub_path)

    # load stuff
    for prefixed_name in loadables:
        sub_context = context.copy()

        # 1. deal with loading. expected pattern: %loadable.<rest>
        unprefixed = prefixed_name[len(LOAD_PREFIX):]
        loadable_name, rest = unprefixed.split('.', 1)

        if loadable_name not in sub_context:
            data = load_data(loadable_name)
            if not isinstance(data, list):
                data = [data]
            for datum in data:
                sub_context[loadable_name] = datum
                do_loadable(site_directory, sub_context, prefixed_name, loadable_name, rest, output_path)
        else:
            do_loadable(site_directory, sub_context, prefixed_name, loadable_name, rest, output_path)


def do_loadable(site_directory, context, prefixed_name, loadable_name, prop, output_path):

    # copying stuff
    if prop.startswith(COPY_PREFIX):
        unprefixed = prop[len(COPY_PREFIX):]
        filenames = context[loadable_name][unprefixed]
        if not isinstance(filenames, list):
            filenames = [filenames]
        for filename in filenames:
            copydata(filename, output_path)

    else:
        sub_dir = os.path.join(site_directory, prefixed_name)
        value = context[loadable_name][prop]
        sub_path = '{}/{}'.format(output_path, value) if output_path else value
        walk_site(sub_dir, context, sub_path)


if __name__ == '__main__':
    walk_site()
