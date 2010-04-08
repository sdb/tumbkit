# -*- coding: utf-8 -*-
"""
Tumbkit is a toolkit to facilitate Tumblr theme development. More information
is available on the home page at http://github.com/sdb/tumbkit and in README.md
"""


import json, re, os, random, sys, getopt, types
import bottle

from os.path import getmtime
from bottle import route, redirect
from datetime import datetime
from HTMLParser import HTMLParser


class Block(object):
    """
    A block is a Python representation of a block in a Tumblr template (theme).
    A block is responsible for resolving variables. A block also decides whether
    or not it's content needs to be rendered.
    """
      
       
    def __init__(self, name, parent = None, output = None, context = None, conf = None, vars = None,  blocks = None):
        """ Creates a block with the given name and parent. """
        
        self.name = name
        self.parent = parent
        self.item = None
        
        self.output = output if parent == None else parent.output
        self.context = context if parent == None else parent.context
        self.conf = conf if parent == None else parent.conf
        self.vars = vars if parent == None else parent.vars
        self.blocks = blocks if parent == None else parent.blocks
     
         
    def resolve_var(self, var_name):
        """
        Returns the value of the given variable.
        """
        
        if self.vars.has_key((self.name, var_name)):
            v = self.vars[self.name, var_name]
            if type(v) is str:
                return v
            elif type(v) is types.FunctionType:
                return v(self, var_name)
        if self.parent != None:
            return self.parent.resolve_var(var_name)
        return None
    
        
    def raw(self, html):
        """ Adds the html to the output. """
        
        self.output.append(html)
    
    
    def var(self, name):
        """ Adds the value of the given variable to the output. """
        
        text = self.resolve_var(name)
        if text == None:
            text = ''
        self.output.append(text)
    
    
    def render(self, render_func):
        """
        This method checks if this block should be executed or not. If so, then
        the given function is executed.
        """
        
        do = False
        b = self
        while not do and b != None:
            if self.blocks.has_key((b.name, self.name)):
                do = True
            else:
                b = b.parent
        if do:
            f = self.blocks[(b.name, self.name)]
            v = f(self, b)
            if type(v) is list:
                for o in v:
                    self.item = o
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

def var_url_safe(v):
    return v.replace(' ', '_') # TODO

    

var_mapping = {        
    ('', 'Title'):                      lambda b, v: b.conf['title'],
    ('', 'Description') :               lambda b, v: b.conf['description'],
    ('', 'MetaDescription') :           lambda b, v: safe_html(b.conf['description']),
    ('', 'RSS') :                       lambda b, v: b.conf['rss'],
    ('', 'Favicon') :                   lambda b, v: b.conf['favicon'],
    ('', 'CustomCSS') :                 lambda b, v: b.conf['css'],
    ('', 'PostTitle') :                 lambda b, v: b.context['posts'][0]['title'],
    ('', 'PostSummary') :               lambda b, v: '', # TODO post summary
    ('Pages', 'URL') :                  lambda b, v: '/%s'%b.item['url'],
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
    ('Posts', 'AmPm') :                 lambda b, v: var_date(b.item['posted'], '%p').lower(),
    ('Posts', 'CapitalAmPm') :          lambda b, v: var_date(b.item['posted'], '%p').upper(),
    ('Posts', '12Hour') :               lambda b, v: str(int(var_date(b.item['posted'], '%I'))),
    ('Posts', '24Hour') :               lambda b, v: str(int(var_date(b.item['posted'], '%H'))),
    ('Posts', '12HourWithZero') :       lambda b, v: var_date(b.item['posted'], '%I'),
    ('Posts', '24HourWithZero') :       lambda b, v: var_date(b.item['posted'], '%H'),
    ('Posts', 'Month') :                lambda b, v: var_date(b.item['posted'], '%B'),
    ('Posts', 'Minutes') :              lambda b, v: var_date(b.item['posted'], '%M'),
    ('Posts', 'Seconds') :              lambda b, v: var_date(b.item['posted'], '%S'),
    ('Posts', 'Beats') :                lambda b, v: var_date(b.item['posted'], '%f'),
    ('Posts', 'Timestamp') :            lambda b, v: '', # TODO Timestamp
    ('Posts', 'ShortMonth') :           lambda b, v: var_date(b.item['posted'], '%b'),
    ('Posts', 'MonthNumberWithZero') :  lambda b, v: var_date(b.item['posted'], '%m'),
    ('Posts', 'MonthNumber') :          lambda b, v: str(int(var_date(b.item['posted'], '%m'))),
    ('Posts', 'DayOfMonthWithZero') :   lambda b, v: var_date(b.item['posted'], '%d'),
    ('Posts', 'DayOfWeek') :            lambda b, v: var_date(b.item['posted'], '%A'),
    ('Posts', 'ShortDayOfWeek') :       lambda b, v: var_date(b.item['posted'], '%a'),
    ('Posts', 'DayOfWeekNumber') :      lambda b, v: var_date(b.item['posted'], '%w'), # TODO should be 1 through 7
    ('Posts', 'DayOfMonth') :           lambda b, v: str(int(var_date(b.item['posted'], '%d'))),
    ('Posts', 'DayOfMonthSuffix') :     lambda b, v: '', # TODO DayOfMonthSuffix
    ('Posts', 'DayOfYear') :            lambda b, v: str(int(var_date(b.item['posted'], '%j'))),
    ('Posts', 'WeekOfYear') :           lambda b, v: str(int(var_date(b.item['posted'], '%W'))),
    ('Posts', 'Year') :                 lambda b, v: var_date(b.item['posted'], '%Y'),
    ('Posts', 'ShortYear') :            lambda b, v: var_date(b.item['posted'], '%y'),
    ('Posts', 'TimeAgo') :              lambda b, v: '%d days ago'%(datetime.now()-datetime.strptime(b.item['posted'], '%Y/%m/%d')).days, # TODO TimeAgo
    ('Posts', 'PostNotes') :            lambda b, v: var_post_notes(b.item['notes']),
    ('Tags', 'Tag') :                   lambda b, v: b.item,
    ('Tags', 'TagURL') :                lambda b, v: '/tagged/%s'%var_url_safe(b.item),
    ('Tags', 'TagURLChrono') :          lambda b, v: '/tagged/%s/chrono'%var_url_safe(b.item),
    ('Tags', 'URLSafeTag') :            lambda b, v: var_url_safe(b.item),
    ('', 'PreviousPage') :              lambda b, v: b.context['pagination']['prev_page'],
    ('', 'NextPage') :                  lambda b, v: b.context['pagination']['next_page'],
    ('', 'TotalPages') :                lambda b, v: '%s'%b.context['total_pages'],
    ('', 'CurrentPage') :               lambda b, v: '%s'%b.context['current_page'],
    ('', 'PreviousPost') :              lambda b, v: var_perma(b.context['permalink_pagination']['prev_post']),
    ('', 'NextPost') :                  lambda b, v: var_perma(b.context['permalink_pagination']['next_post']),
}

for dim in [16,24,30,40,48,64,96,128]:
    var_mapping[('', 'PortraitURL-%d'%dim)] = 'http://assets.tumblr.com/images/default_avatar_%d.gif'%dim


block_mapping = {
    ('', 'Description') :           lambda b, p: p.conf.has_key('description'),
    ('', 'PermalinkPage') :         lambda b, p: p.context['type'] == 'perma',
    ('', 'IndexPage') :             lambda b, p: p.context['type'] == 'index',
    ('', 'PostTitle') :             lambda b, p: p.context.has_key('posts') and len(p.context['posts']) > 0 and p.context['posts'][0].has_key('title'),
    ('', 'PostSummary') :           lambda b, p: p.context.has_key('posts') and len(p.context['posts']) > 0,
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
    ('Posts', 'Chat') :             lambda b, p: p.item['type'].capitalize() == b.name,
    ('Posts', 'Date') :             lambda b, p: True,
    # TODO PostNotes ('Posts', 'PostNotes') :        lambda b, p: p.item.has_key('notes') and len(p.item['notes']) > 0,
    ('', 'Pagination') :            lambda b, p: p.context.has_key('pagination'),
    ('', 'PreviousPage') :          lambda b, p: p.context['pagination']['prev_page'],
    ('', 'NextPage') :              lambda b, p: p.context['pagination']['next_page'],
    ('', 'PermalinkPagination') :   lambda b, p: p.context.has_key('permalink_pagination'),
    ('', 'PreviousPost') :          lambda b, p: p.context['permalink_pagination']['prev_post'],
    ('', 'NextPost') :              lambda b, p: p.context['permalink_pagination']['next_post'],
}


def create_conf(conf_file):
    return json.load(open(conf_file, 'r'))


def create_blocks(conf):
    """ """
    
    blocks = {}
    blocks.update(block_mapping)
    for v in conf['variables']:
        if v.startswith('if:'):
            var = ''
            for s in v.split(':')[1].split(' '):
                var += s.capitalize()
            blocks[('', 'If%s'%var)] = lambda b, p: conf['variables'][v] == 1
            blocks[('', 'IfNot%s'%var)] = lambda b, p: conf['variables'][v] != 1
        else:
            var = ''
            for s in v.split(':')[1].split(' '):
                var += s.capitalize()
            blocks[('', 'If%s'%var)] = lambda b, p: True
    return blocks

            
def create_vars(conf):
    """ """
    
    vars = {}
    vars.update(var_mapping)
    for v in conf['variables']:
        vars[('', v)] = lambda b, v: conf['variables'][v] 
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
        block = Block('', output = output, context = context, conf = self.conf, vars = create_vars(self.conf), blocks = create_blocks(self.conf))
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
            "prev_page" : '%s/page/%s'%(url_prefix, prev) if prev != None else None,
            "next_page" : '%s/page/%s'%(url_prefix, next) if next != None else None
        }
    return context


@route('/')
@route('/page/:pagenr')
def index(pagenr = 1):
    """ Index page. """
    
    def prepare_context(conf):
        context = {}
        posts_per_page = conf['post_per_page']
        posts = sorted(conf['posts'], key=lambda k: datetime.strptime(k['posted'], '%Y/%m/%d'), reverse=True)[(pagenr-1)*posts_per_page:(posts_per_page*pagenr)]
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


@route('/search/:query')
def search(query):
    """ """
    
    return 'Not yet supported'


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
        posts = sorted(posts, key=lambda k: datetime.strptime(k['posted'], '%Y/%m/%d'), reverse=True)
        context['type'] = 'tagged'
        return prepare_context_for_posts(posts_per_page, pagenr, len(posts), posts, context, '/tagged/%s'%tag)
    
    pagenr = int(pagenr)
    return engine.apply(prepare_context)


@route('/:page')
def page(page): # TODO mapping should only include known pages
    """ """
    
    return 'Not yet supported'
    

    
def usage():
    """ Prints usage message. """
    
    None # TODO print usage message

   
def main(argv):
    """ Parses the command line arguments and starts the server. """
    
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
    