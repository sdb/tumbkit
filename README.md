Tumbkit
=======

Tumbkit is a toolkit to facilitate [Tumblr][t] theme development. 

Note that this is still a work in progress and at the moment not all
functionality is implemented. See the feature overview below for more
information.


Usage
-----

Tumbkit offers a server which serves your custom Tumblr template (theme).
This allows you to develop the themes on your local machine. All you have
to do is to create a configuration file in JSON format that contains some
sample data and then you're ready to go (see the sample_cfg.json file for
an example configuration file).

To start the server execute the following command:

    python tumbkit.py [-t tpl] [-c cfg]

    -t : path to the template file, which defaults to ./tpl.html
    -c : path to the configuration file, which defaults to ./cfg.json

Now go to [http://localhost:8080/](http://localhost:8080/) to see your template
in action.

Features
--------

* a mini-server for developing and testing Tumblr themes 
* changes to the configuration and template (theme) file are automatically
visible in your browser, no need to restart the server
* easy configuration in JSON format

This is still a work in progress. Let's see what we've got currently:

URL's:

* index pages ('/' and '/page/$pagenr')
* post (permalink) pages ('/posts/$postid/$perma')
* tag pages ('/tagged/$tag' and '/tagged/$tag/page/$pagenr')
* random page ('/random')

Theme:

* all basic variables, except PostSummary
* text, link, chat and quote posts
* pagination (not yet for day pages)
* variables for custom pages
* all date variables
* tags for posts
* ...

Not yet:

* reblogged, notes
* followings
* search (page)
* day pages
* photo, audio, video, answer posts
* ...


Dependencies
------------

* the Python Standard library
* [bottle][b] framework

License
-------

This work is licensed under the [MIT license][m].


[t]:http://www.tumblr.com/
[m]:http://www.opensource.org/licenses/mit-license.php
[b]:http://github.com/defnull/bottle
