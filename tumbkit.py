# -*- coding: utf-8 -*-
"""
Tumbkit is a toolkit to facilitate Tumblr theme development. More information is available
on the home page at http://github.com/sdb/tumbkit.

This work is licensed under the MIT license (see LICENSE).
"""


import json, re, os, random, sys, getopt
import bottle

from os.path import getmtime
from bottle import route
from datetime import datetime


class Block(object):
    
    def __init__(self, name, parent):
        self.name = name
        self.parent = parent
        self.item = None
        if parent != None:
            self.output = parent.output
        
    def get_root(self):
        """ """
        b = self
        while b.parent != None:
            b = b.parent
        return b
        
    def resolve_var(self, var_name):
        """ """
        
        if self.get_root().vars.has_key((self.name, var_name)):
            return self.get_root().vars[self.name, var_name](self, var_name)
        if self.parent != None:
            return self.parent.resolve_var(var_name)
        return None
    
    def raw(self, html):
        """ """
        
        self.output.append(html)
        
    def newline(self):
        """ """
        
        self.output.append('\n')
    
    def var(self, name):
        """ """
        
        text = self.resolve_var(name)
        if text == None:
            text = ''
        self.output.append(text)
    
    def render(self, render_func):
        """ """
        
        do = False
        b = self
        while not do and b != None:
            if self.get_root().blocks.has_key((b.name, self.name)):
                do = True
            else:
                b = b.parent
        if do:
            f = self.get_root().blocks[(b.name, self.name)]
            v = f(self, b)
            if type(v) is list:
                for o in v:
                    self.item = o
                    render_func(self)
            elif v:
                render_func(self)
                
        
class RootBlock(Block):
    
    def __init__(self, name, context, conf, vars, blocks):
        super(RootBlock, self).__init__(name, None)
        self.context = context
        self.conf = conf
        self.vars = vars
        self.blocks = blocks
        self.output = []


def create_script(tpl_file):
    lines = []
    tpl = open(tpl_file)
    indent = 0
    func_ids = {}
    id_stack = []
    for line in tpl.readlines():
        line = line.rstrip(os.linesep)
        parts = re.split('(\\{.*?\\})', line)
        for part in parts:
            if part.startswith('{block:'):
                name = part[7:len(part) - 1]
                if func_ids.has_key(name):
                    id = func_ids[name] + 1
                    func_ids[name] = id
                else:
                    id = 1
                    func_ids[name] = id
                id_s = '%s_%d'%(name, id)
                id_stack.append(id_s)
                lines.append('%sblock = Block(\'%s\', parent = block)'%('\t' * indent, name))
                lines.append('%sdef block_%s(block):'%('\t' * indent, id_s))
                indent += 1
            elif part.startswith('{/block:'):
                indent -= 1
                lines.append('%sblock.render(block_%s)'%('\t' * indent, id_stack.pop()))
                lines.append('%sblock = block.parent'%('\t' * indent))
            elif part.startswith('{'):
                lines.append('%sblock.var(\'%s\')'%('\t' * indent, part[1:len(part) - 1]))
            else:
                if len(part) > 0:
                    lines.append('%sblock.raw(\'%s\')'%('\t' * indent, part.replace('\'', '\\\'')))
                    
    return '\n'.join(lines)


def var_date(s, fmt):
    d = datetime.strptime(s, '%Y/%m/%d')
    return d.strftime(fmt)

def var_perma(post):
    if post.has_key('title'):
        p = post['title']
    else:
        p = 'summary' # TODO post summary
    return '/post/%d/%s'%(post['id'], p.replace(' ', '-').lower())

def var_name(post):
    if post.has_key('title'):
        return post['title']
    else:
        return post['url']

var_mapping = {        
    ('', 'Title'):                      lambda b, v: b.conf['title'],
    ('', 'Description') :               lambda b, v: b.conf['description'],
    ('', 'RSS') :                       lambda b, v: b.conf['rss'],
    ('', 'Favicon') :                   lambda b, v: b.conf['favicon'],
    ('', 'CustomCSS') :                 lambda b, v: b.conf['css'],
    ('', 'PostTitle') :                 lambda b, v: b.context['posts'][0]['title'],
    ('', 'PostSummary') :               lambda b, v: b.context['posts'][0]['summary'], # TODO
    ('Pages', 'URL') :                  lambda b, v: b.item['url'],
    ('Pages', 'Label') :                lambda b, v: b.item['title'],
    ('Posts', 'Permalink') :            lambda b, v: var_perma(b.item),
    ('Posts', 'Title') :                lambda b, v: b.item['title'],
    ('Posts', 'Body') :                 lambda b, v: b.item['body'],
    ('Posts', 'Description') :          lambda b, v: b.item['description'],
    ('Posts', 'Name') :                 lambda b, v: var_name(b.item),
    ('Posts', 'Quote') :                lambda b, v: b.item['quote'],
    ('Posts', 'Source') :               lambda b, v: b.item['source'],
    ('Lines', 'Line') :                 lambda b, v: b.item['text'],
    ('Lines', 'Label') :                lambda b, v: b.item['label'],
    ('Posts', 'Month') :                lambda b, v: var_date(b.item['posted'], '%B'),
    ('Posts', 'ShortMonth') :           lambda b, v: var_date(b.item['posted'], '%b'),
    ('Posts', 'MonthNumberWithZero') :  lambda b, v: var_date(b.item['posted'], '%m'),
    ('Posts', 'DayOfMonthWithZero') :   lambda b, v: var_date(b.item['posted'], '%d'),
    ('Posts', 'DayOfMonth') :           lambda b, v: var_date(b.item['posted'], '%d'),
    ('Posts', 'Year') :                 lambda b, v: var_date(b.item['posted'], '%Y'),
    ('Posts', 'TimeAgo') :              lambda b, v: '%d days ago'%(datetime.now()-datetime.strptime(b.item['posted'], '%Y/%m/%d')).days,
    ('Tags', 'Tag') :                   lambda b, v: b.item,
    ('Tags', 'TagURL') :                lambda b, v: '/tagged/%s'%b.item
}

block_mapping = {
    ('', 'Description') :           lambda b, p: p.conf.has_key('description'),
    ('', 'PermalinkPage') :         lambda b, p: p.context.has_key('description'),
    ('', 'PostTitle') :             lambda b, p: p.context.has_key('posts') and len(p.context['posts']) > 0 and p.context['posts'][0].has_key('title'),
    ('', 'HasPages') :              lambda b, p: p.conf.has_key('pages'),
    ('', 'Pages') :                 lambda b, p: p.conf['pages'],
    ('', 'Posts') :                 lambda b, p: p.context['posts'],
    ('Posts', 'Title') :            lambda b, p: p.item.has_key('title'),
    ('Posts', 'HasTags') :          lambda b, p: p.item.has_key('tags'),
    ('Posts', 'Tags') :             lambda b, p: p.item['tags'],
    ('Posts', 'Lines') :            lambda b, p: p.item['dialogue'],
    ('Lines', 'Label') :            lambda b, p: p.item.has_key('label'),
    ('Posts', 'Text') :             lambda b, p: p.item['type'].capitalize() == b.name,
    ('Posts', 'Quote') :            lambda b, p: p.item['type'].capitalize() == b.name,
    ('Posts', 'Source') :           lambda b, p: p.item.has_key('source'),
    ('Posts', 'Link') :             lambda b, p: p.item['type'].capitalize() == b.name,
    ('Posts', 'Chat') :             lambda b, p: p.item['type'].capitalize() == b.name
}


def create_conf(conf_file):
    return json.load(open(conf_file, 'r'))


def create_blocks(conf):
    blocks = {}
    blocks.update(block_mapping)
    for v in conf['variables']:
        if v.startswith('if:'):
            var = ''
            for s in v.split(':')[1].split(' '):
                var += s.capitalize()
            blocks[('', 'If%s'%var)] = lambda b, p: conf['variables'][v] == 1
            blocks[('', 'NotIf%s'%var)] = lambda b, p: conf['variables'][v] != 1
        else:
            var = ''
            for s in v.split(':')[1].split(' '):
                var += s.capitalize()
            blocks[('', 'If%s'%var)] = lambda b, p: True
    return blocks
            
def create_vars(conf):
    vars = {}
    vars.update(var_mapping)
    for v in conf['variables']:
        vars[('', v)] = lambda b, v: conf['variables'][v] 
    return vars
        

class Engine:
    
    def __init__(self, tpl_file, conf_file):
        self.tpl_file = tpl_file
        self.tpl_mod = None
        self.script = None
        self.conf_file = conf_file
        self.conf_mod = None
        self.conf = None
         
    def prepare(self):
        if self.script == None or getmtime(self.tpl_file) != self.tpl_mod:
            self.script = create_script(self.tpl_file)
            self.tpl_mod = getmtime(self.tpl_file)
        if self.conf == None or getmtime(self.conf_file) != self.conf_mod:
            self.conf = create_conf(self.conf_file)
            self.conf_mod = getmtime(self.conf_file)
            
    def render(self, prepare_context):
        self.prepare()
        context = prepare_context(self.conf)
        block = RootBlock('', context, self.conf, create_vars(self.conf), create_blocks(self.conf))
        exec(self.script)
        return ''.join(block.output)

    
@route('/')
def index():
    def prepare_context(conf):
        context = {}
        posts_per_page = conf['post_per_page']
        context['posts'] = conf['posts'][0:posts_per_page]
        context['index'] = True
        context['perma'] = False
        return context
    return engine.render(prepare_context)

@route('/page/:number')
def index_page(number):
    def prepare_context(conf):
        context = {}
        page = int(number)
        posts_per_page = conf['post_per_page']
        context['posts'] = conf['posts'][(page-1)*posts_per_page:(posts_per_page*page)]
        context['index'] = True
        context['perma'] = False
        return context
    return engine.render(prepare_context)

@route('/post/:id/:perma')
def post(id, perma):
    def prepare_context(conf):
        context = {}
        for post in conf['posts']:
            if post['id'] == int(id):
                context['posts'] = [post]
                context['perma'] = True
                context['index'] = False
                return context
    return engine.render(prepare_context)

@route('/random')
def random_post():
    def prepare_context(conf):
        context = {}
        context['posts'] = [conf['posts'][(random.randint(0, len(conf['posts']) - 1))]]
        context['perma'] = True
        context['index'] = False
        return context
    return engine.render(prepare_context)

@route('/archive')
def archive():
    return 'Not yet supported'

@route('/search/:query')
def search(query):
    return 'Not yet supported'

@route('/day/:year/:month/:day')
def day(year, month, day):
    return 'Not yet supported'

@route('/tagged/:tag')
def tagged(tag):
    return 'Not yet supported'

@route('/:page')
def page(page):
    return 'Not yet supported'
    
    
def usage():
    """ prints usage message """
    
    None # TODO print usage message
    
def main(argv):
    """ parses the command line arguments and starts the server """
    
    tpl = './tpl.html'        
    cfg = './cfg.json'
    debug = False
    
    try:
        opts, args = getopt.getopt(argv, 'ht:c:d', ['help', 'tpl=', 'cfg='])                               
    except getopt.GetoptError:
        usage()          
        sys.exit(2)                     
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit()                  
        elif opt == '-d':                
            debug = True              
        elif opt in ('-t', '--tpl'): 
            tpl = arg
        elif opt in ('-c', '--cfg'): 
            cfg = arg
    
    global engine
    engine = Engine(tpl, cfg)
    bottle.debug(debug)
    bottle.run()
    
    
if __name__ == '__main__':
    main(sys.argv[1:])
    