# -*- coding: utf-8 -*-
"""
Tumbkit is a toolkit to facilitate Tumblr theme development. More information
is available on the home page at http://github.com/sdb/tumbkit and in README.md
"""


import json, re, os, random, sys, getopt, types
import bottle

from os.path import getmtime
from bottle import route, redirect, request
from datetime import datetime
from HTMLParser import HTMLParser


class Block(object):
    """
    A block is a Python representation of a block in a Tumblr template (theme).
    """
      
       
    def __init__(self, name, parent):
        """ Creates a block with the given name and parent. """
        
        self.name = name
        self.parent = parent
        self.item = None
                

class Renderer(object):
    """
    A renderer is responsible for resolving variables. A renderer also decides
    whether or not a block needs to be rendered.
    """
    
    def __init__(self, output, context, conf, vars, blocks):
        
        self.output = output
        self.context = context
        self.conf = conf
        self.vars = vars
        self.blocks = blocks
        self.block = Block('', None)
        
        
    def resolve_var(self, var_name, block):
        """
        Returns the value of the given variable for the given block.
        """
        
        if self.vars.has_key((block.name, var_name)):
            v = self.vars[block.name, var_name]
            if type(v) is str:
                return v
            elif type(v) is types.FunctionType:
                return v(block, var_name, self)
        if block.parent != None:
            return self.resolve_var(var_name, block.parent)
        return None
    
    
    def raw(self, html):
        """ Adds the html to the output. """
        
        self.output.append(html)
    
    
    def var(self, name):
        """
        Adds the value of the given variable in the given block to the output.
        """
        
        text = self.resolve_var(name, self.block)
        self.output.append('' if text == None else str(text))
        
        
    def render(self, render_func):
        """
        This method checks if the given block should be executed or not. If so,
        then the given function is executed.
        """
        
        do = False
        b = self.block
        while not do and b != None:
            if self.blocks.has_key((b.name, self.block.name)):
                do = True
            else:
                b = b.parent
        if do:
            f = self.blocks[(b.name, self.block.name)]
            v = f(self.block, b, self)
            if type(v) is list:
                for o in v:
                    self.block.item = o
                    render_func(self)
            elif v:
                render_func(self)
        
        

class HtmlStripper(HTMLParser):
    """ """
    
    def __init__(self):
        self.reset()
        self.data = []
         
    def handle_data(self, d):
         self.data.append(d)
         
    def get_data(self):
         return ''.join(self.data)
   
   
def safe_html(s):
    """ """
    
    stripper = HtmlStripper()
    stripper.feed(s)
    return stripper.get_data()

def var_perma(post):
    p = post['title'] if post.has_key('title') else 'summary' # TODO post summary
    return '/post/%d/%s'%(post['id'], p.replace(' ', '-').lower())

def var_url_safe(v):
    return v.replace(' ', '_') # TODO

    

var_mapping = {        
    ('', 'Title'):                      lambda b, v, r: r.conf['title'],
    ('', 'Description') :               lambda b, v, r: r.conf['description'],
    ('', 'MetaDescription') :           lambda b, v, r: safe_html(r.conf['description']),
    ('', 'RSS') :                       lambda b, v, r: r.conf['rss'],
    ('', 'Favicon') :                   lambda b, v, r: r.conf['favicon'],
    ('', 'CustomCSS') :                 lambda b, v, r: r.conf['css'],
    ('', 'PostTitle') :                 lambda b, v, r: r.context['posts'][0]['title'],
    ('', 'PostSummary') :               lambda b, v, r: '', # TODO post summary
    ('Pages', 'URL') :                  lambda b, v, r: '/%s'%b.item['url'],
    ('Pages', 'Label') :                lambda b, v, r: b.item['title'],
    ('Posts', 'Permalink') :            lambda b, v, r: var_perma(b.item),
    ('Posts', 'Title') :                lambda b, v, r: b.item['title'],
    ('Posts', 'Body') :                 lambda b, v, r: b.item['body'],
    ('Posts', 'Description') :          lambda b, v, r: b.item['description'],
    ('Posts', 'Name') :                 lambda b, v, r: b.item['title'] if b.item.has_key('title') else b.item['url'],
    ('Posts', 'Quote') :                lambda b, v, r: b.item['quote'],
    ('Posts', 'Source') :               lambda b, v, r: b.item['source'],
    ('Lines', 'Line') :                 lambda b, v, r: b.item['text'],
    ('Lines', 'Label') :                lambda b, v, r: b.item['label'],
    ('Posts', 'AmPm') :                 lambda b, v, r: b.item['posted'].strftime('%p').lower(),
    ('Posts', 'CapitalAmPm') :          lambda b, v, r: b.item['posted'].strftime('%p').upper(),
    ('Posts', '12Hour') :               lambda b, v, r: str(int(b.item['posted'].strftime('%I'))),
    ('Posts', '24Hour') :               lambda b, v, r: str(int(b.item['posted'].strftime('%H'))),
    ('Posts', '12HourWithZero') :       lambda b, v, r: b.item['posted'].strftime('%I'),
    ('Posts', '24HourWithZero') :       lambda b, v, r: b.item['posted'].strftime('%H'),
    ('Posts', 'Month') :                lambda b, v, r: b.item['posted'].strftime('%B'),
    ('Posts', 'Minutes') :              lambda b, v, r: b.item['posted'].strftime('%M'),
    ('Posts', 'Seconds') :              lambda b, v, r: b.item['posted'].strftime('%S'),
    ('Posts', 'Beats') :                lambda b, v, r: b.item['posted'].strftime('%f'),
    ('Posts', 'Timestamp') :            lambda b, v, r: '', # TODO Timestamp
    ('Posts', 'ShortMonth') :           lambda b, v, r: b.item['posted'].strftime('%b'),
    ('Posts', 'MonthNumberWithZero') :  lambda b, v, r: b.item['posted'].strftime('%m'),
    ('Posts', 'MonthNumber') :          lambda b, v, r: str(int(b.item['posted'].strftime('%m'))),
    ('Posts', 'DayOfMonthWithZero') :   lambda b, v, r: b.item['posted'].strftime('%d'),
    ('Posts', 'DayOfWeek') :            lambda b, v, r: b.item['posted'].strftime('%A'),
    ('Posts', 'ShortDayOfWeek') :       lambda b, v, r: b.item['posted'].strftime('%a'),
    ('Posts', 'DayOfWeekNumber') :      lambda b, v, r: b.item['posted'].strftime('%w'), # TODO should be 1 through 7
    ('Posts', 'DayOfMonth') :           lambda b, v, r: str(int(b.item['posted'].strftime('%d'))),
    ('Posts', 'DayOfMonthSuffix') :     lambda b, v, r: '', # TODO DayOfMonthSuffix
    ('Posts', 'DayOfYear') :            lambda b, v, r: str(int(b.item['posted'].strftime('%j'))),
    ('Posts', 'WeekOfYear') :           lambda b, v, r: str(int(b.item['posted'].strftime('%W'))),
    ('Posts', 'Year') :                 lambda b, v, r: b.item['posted'].strftime('%Y'),
    ('Posts', 'ShortYear') :            lambda b, v, r: b.item['posted'].strftime('%y'),
    ('Posts', 'TimeAgo') :              lambda b, v, r: '%d days ago'%(datetime.now()-b.item['posted']).days, # TODO TimeAgo
    ('Posts', 'PostNotes') :            lambda b, v, r: var_post_notes(b.item['notes']),
    ('Tags', 'Tag') :                   lambda b, v, r: b.item,
    ('Tags', 'TagURL') :                lambda b, v, r: '/tagged/%s'%var_url_safe(b.item),
    ('Tags', 'TagURLChrono') :          lambda b, v, r: '/tagged/%s/chrono'%var_url_safe(b.item),
    ('Tags', 'URLSafeTag') :            lambda b, v, r: var_url_safe(b.item),
    ('', 'PreviousPage') :              lambda b, v, r: r.context['pagination']['prev_page'],
    ('', 'NextPage') :                  lambda b, v, r: r.context['pagination']['next_page'],
    ('', 'TotalPages') :                lambda b, v, r: '%s'%r.context['total_pages'],
    ('', 'CurrentPage') :               lambda b, v, r: '%s'%r.context['current_page'],
    ('', 'PreviousPost') :              lambda b, v, r: var_perma(r.context['permalink_pagination']['prev_post']),
    ('', 'NextPost') :                  lambda b, v, r: var_perma(r.context['permalink_pagination']['next_post']),
    ('', 'Tag') :                       lambda b, v, r: r.context['tag'],
    ('', 'TagURL') :                    lambda b, v, r: '/tagged/%s'%var_url_safe(r.context['tag']),
    ('', 'TagURLChrono') :              lambda b, v, r: '/tagged/%s/chrono'%var_url_safe(r.context['tag']),
    ('', 'URLSafeTag') :                lambda b, v, r: var_url_safe(r.context['tag']),
    ('', 'SearchQuery') :               lambda b, v, r: r.context['query'],
    ('', 'URLSafeSearchQuery') :        lambda b, v, r: var_url_safe(r.context['query']),
    ('', 'SearchResultCount') :         lambda b, v, r: r.context['result_count'],
}

for dim in [16,24,30,40,48,64,96,128]:
    var_mapping[('', 'PortraitURL-%d'%dim)] = 'http://assets.tumblr.com/images/default_avatar_%d.gif'%dim


block_mapping = {
    ('', 'Description') :           lambda b, p, r: r.conf.has_key('description'),
    ('', 'PermalinkPage') :         lambda b, p, r: r.context['type'] == 'perma',
    ('', 'IndexPage') :             lambda b, p, r: r.context['type'] == 'index',
    ('', 'PostTitle') :             lambda b, p, r: r.context['type'] == 'perma' and r.context.has_key('posts') and len(r.context['posts']) > 0 and r.context['posts'][0].has_key('title'),
    ('', 'PostSummary') :           lambda b, p, r: r.context.has_key('posts') and len(r.context['posts']) > 0,
    ('', 'HasPages') :              lambda b, p, r: r.conf.has_key('pages'),
    ('', 'Pages') :                 lambda b, p, r: r.conf['pages'],
    ('', 'Posts') :                 lambda b, p, r: r.context['posts'],
    ('Posts', 'Title') :            lambda b, p, r: p.item.has_key('title'),
    ('Posts', 'HasTags') :          lambda b, p, r: p.item.has_key('tags'),
    ('Posts', 'Tags') :             lambda b, p, r: p.item['tags'],
    ('Posts', 'Lines') :            lambda b, p, r: p.item['dialogue'],
    ('Lines', 'Label') :            lambda b, p, r: p.item.has_key('label'),
    ('Posts', 'Text') :             lambda b, p, r: p.item['type'].capitalize() == b.name,
    ('Posts', 'Quote') :            lambda b, p, r: p.item['type'].capitalize() == b.name,
    ('Posts', 'Source') :           lambda b, p, r: p.item.has_key('source'),
    ('Posts', 'Link') :             lambda b, p, r: p.item['type'].capitalize() == b.name,
    ('Posts', 'Chat') :             lambda b, p, r: p.item['type'].capitalize() == b.name,
    ('Posts', 'Date') :             lambda b, p, r: True,
    # TODO PostNotes ('Posts', 'PostNotes') :        lambda b, p, r: p.item.has_key('notes') and len(p.item['notes']) > 0,
    ('', 'Pagination') :            lambda b, p, r: r.context.has_key('pagination'),
    ('', 'PreviousPage') :          lambda b, p, r: r.context['pagination']['prev_page'],
    ('', 'NextPage') :              lambda b, p, r: r.context['pagination']['next_page'],
    ('', 'PermalinkPagination') :   lambda b, p, r: r.context.has_key('permalink_pagination'),
    ('', 'PreviousPost') :          lambda b, p, r: r.context['permalink_pagination']['prev_post'],
    ('', 'NextPost') :              lambda b, p, r: r.context['permalink_pagination']['next_post'],
    ('', 'TagPage') :               lambda b, p, r: r.context['type'] == 'tagged',
    ('', 'SearchPage') :            lambda b, p, r: r.context['type'] == 'search',
    ('', 'NoSearchResults') :       lambda b, p, r: r.context['result_count'] == 0,
}


def create_conf(conf_file):
    
    def override_copy(key, src, dest):
        if key == 'posted' and type(src[key]) is unicode:
            dest[key] = datetime.strptime(src[key], '%Y/%m/%d')
            return True
        elif key == 'dialogue':
            dest[key] = []
            for i, e in enumerate(src[key]):
                if type(e) is unicode:
                    s = e.split(':')
                    dest[key].append({})
                    if len(s) > 1:
                        dest[key][i]['label'] = s[0]
                        dest[key][i]['text'] = s[1]
                    else:
                        dest[key][i]['label'] = None
                        dest[key][i]['text'] = s[1]
                else:
                    copy_conf(i, src[key], dest[key])
            return True
        return False
    
    def copy_conf(key, src, dest):
        if override_copy(key, src, dest):
            return
        
        if type(src[key]) is dict:  
            v = {}
            for k in src[key]:
                copy_conf(k, src[key], v)
        elif type(src[key]) is list:
            v = []
            for i, e in enumerate(src[key]):
                copy_conf(i, src[key], v)
        else:
            v = src[key]
        
        if type(key) is int:
            dest.append(v)
        else:    
            dest[key] = v
            
    
    conf = json.load(open(conf_file, 'r'))
    
    copy = {}
    for k in conf:
        copy_conf(k, conf, copy)            
        
    return copy


def create_blocks(conf):
    """ """
    
    blocks = {}
    blocks.update(block_mapping)
    for v in conf['variables']:
        if v.startswith('if:'):
            var = ''
            for s in v.split(':')[1].split(' '):
                var += s.capitalize()
            blocks[('', 'If%s'%var)] = lambda b, p, r: conf['variables'][v] == 1
            blocks[('', 'IfNot%s'%var)] = lambda b, p, r: conf['variables'][v] != 1
        else:
            var = ''
            for s in v.split(':')[1].split(' '):
                var += s.capitalize()
            blocks[('', 'If%s'%var)] = lambda b, p, r: True
    return blocks

            
def create_vars(conf):
    """ """
    
    vars = {}
    vars.update(var_mapping)
    for v in conf['variables']:
        vars[('', v)] = lambda b, v, r: conf['variables'][v] 
    return vars


def create_script(tpl_file):
    """ """
    
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
                lines.append('%srenderer.block = Block(\'%s\', parent = renderer.block)'%('\t' * indent, name))
                lines.append('%sdef block_%s(renderer):'%('\t' * indent, id_s))
                indent += 1
            elif part.startswith('{/block:'):
                indent -= 1
                lines.append('%srenderer.render(block_%s)'%('\t' * indent, id_stack.pop()))
                lines.append('%srenderer.block = renderer.block.parent'%('\t' * indent))
            elif part.startswith('{'):
                lines.append('%srenderer.var(\'%s\')'%('\t' * indent, part[1:len(part) - 1]))
            else:
                if len(part) > 0:
                    lines.append('%srenderer.raw(\'%s\')'%('\t' * indent, part.replace('\'', '\\\'')))
                    
    return '\n'.join(lines)
        


class Engine:
    """ """
    
    def __init__(self, tpl_file, cfg_file):
        """ """
        
        self.tpl = (tpl_file, None)
        self.script = None
        self.cfg = (cfg_file, None)
        self.conf = None
            
            
    def apply(self, prepare_context):
        """ """
        
        if self.script == None or getmtime(self.tpl[0]) != self.tpl[1]:
            self.script = create_script(self.tpl[0])
            self.tpl = (self.tpl[0], getmtime(self.tpl[0]))
            
        if self.conf == None or getmtime(self.cfg[0]) != self.cfg[1]:
            self.conf = create_conf(self.cfg[0])
            self.cfg = (self.cfg[0], getmtime(self.cfg[0]))
            
        context = prepare_context(self.conf)
        output = []
        renderer = Renderer(output, context,self.conf, create_vars(self.conf), create_blocks(self.conf))
        exec(self.script)
        
        return ''.join(output)



def prepare_context_for_posts(posts_per_page, pagenr, total_posts, posts, context, url_prefix):
    total_pages = (total_posts / posts_per_page) +  (0 if total_posts % posts_per_page == 0 else 1)
    context['posts'] = posts
    context['total_pages'] = total_pages
    context['current_page'] = pagenr
    prev = pagenr - 1 if pagenr > 1 else None
    next = pagenr + 1 if pagenr < total_pages else None
    if prev != None or next != None:
        context['pagination'] = {
            'prev_page' : '%s/page/%s'%(url_prefix, prev) if prev != None else None,
            'next_page' : '%s/page/%s'%(url_prefix, next) if next != None else None
        }
    return context


@route('/')
@route('/page/:pagenr')
def index(pagenr = 1):
    """ Index page. """
    
    def prepare_context(conf):
        context = {}
        posts_per_page = conf['post_per_page']
        posts = sorted(conf['posts'], key=lambda k: k['posted'], reverse=True)[(pagenr-1)*posts_per_page:(posts_per_page*pagenr)]
        context['type'] = 'index'
        return prepare_context_for_posts(posts_per_page, pagenr, len(conf['posts']), posts, context, '')
    
    pagenr = int(pagenr)
    return engine.apply(prepare_context)


@route('/post/:id/:perma')
def post(id, perma):
    """ Permalink page showing post with specified id """
    
    def prepare_context(conf):
        context = {}
        for i, p in enumerate(conf['posts']):
            if p['id'] == int(id):
                break
        context['posts'] = [p]
        context['type'] = 'perma'
        context['permalink_pagination'] = {} if len(conf['posts']) > 0 else None
        context['permalink_pagination']['prev_post'] = conf['posts'][i-1] if i > 0 else None
        context['permalink_pagination']['next_post'] = conf['posts'][i+1] if i < len(conf['posts'])-1 else None
        return context
    
    return engine.apply(prepare_context)


@route('/random')
def random_post():
    """ Redirects to permalink of random post. """
    
    post = engine.conf['posts'][(random.randint(0, len(engine.conf['posts']) - 1))]
    if post.has_key('title'):
        p = post['title']
    else:
        p = 'summary' # TODO post summary
    redirect('/post/%d/%s'%(post['id'], p.replace(' ', '-').lower()))


@route('/archive')
def archive():
    """ """
    
    return 'Not supported'


@route('/search/:query/page/:pagenr')
@route('/search/:query')
@route('/search', method='GET')
def search(query = None, pagenr = 1):
    """ The 'fake' search page. """
    
    def prepare_context(conf):
        context = {}
        posts_per_page = conf['post_per_page']
        if query == 'noresult':
            posts = []
        else:
            posts = conf['posts']
        posts = sorted(posts, key=lambda k: k['posted'], reverse=True)
        context['type'] = 'search'
        context['query'] = query
        context['result_count'] = len(posts)
        return prepare_context_for_posts(posts_per_page, pagenr, len(posts), posts[(pagenr-1)*posts_per_page:(posts_per_page*pagenr)], context, '/search/%s'%query)
    
    pagenr = int(pagenr)
    if not query:
        query = request.GET.get('q', '').strip()
    return engine.apply(prepare_context)


@route('/day/:year/:month/:day')
def day(year, month, day):
    """ """
    
    return 'Not yet supported'


@route('/tagged/:tag/page/:pagenr')
@route('/tagged/:tag')
def tagged(tag, pagenr = 1):
    """ """
    
    def prepare_context(conf):
        context = {}
        posts_per_page = conf['post_per_page']
        posts = []
        for p in conf['posts']:
            if p.has_key('tags') and tag in p['tags']:
                posts.append(p)
        posts = sorted(posts, key=lambda k: k['posted'], reverse=True)
        context['type'] = 'tagged'
        context['tag'] = tag
        return prepare_context_for_posts(posts_per_page, pagenr, len(posts), posts[(pagenr-1)*posts_per_page:(posts_per_page*pagenr)], context, '/tagged/%s'%tag)
    
    pagenr = int(pagenr)
    return engine.apply(prepare_context)


@route('/:page')
def page(page): # TODO mapping should only include known pages
    """ """
    
    return 'Not yet supported'
    

    
def usage():
    """ Prints usage message. """
    
    print 'Usage: python tumbkit.py -d [-t tpl] [-c cfg] [-p port]'
    print 'Options and arguments:'
    print '-t  : path to the template file, defaults to ./tpl.html'
    print '-c  : path to the configuration file, defaults to ./cfg.json'
    print '-p  : port, defaults to 8080'
    print '-d  : debug, defaults to False'

   
def main(argv, tpl = './tpl.html', cfg = './cfg.json', debug = False, port = 8080):
    """ Parses the command line arguments and starts the server. """
    
    try:
        opts, args = getopt.getopt(argv, 'ht:c:p:d', ['help', 'tpl=', 'cfg=', 'port='])                               
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
        elif opt in ('-p', '--port'):
            port = arg
    
    global engine
    engine = Engine(tpl, cfg)
    bottle.debug(debug)
    bottle.run(host='localhost', port=port)
    
    
if __name__ == '__main__':
    main(sys.argv[1:])

    