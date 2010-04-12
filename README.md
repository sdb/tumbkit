Tumbkit
=======

Tumbkit is a utility script to facilitate [Tumblr][t] theme development. 

Note that this is still a work in progress and at the moment not all
functionality is implemented. See the feature overview below for more
information.

Tumbkit offers a server which serves your custom Tumblr template (theme).
This allows you to develop the themes on your local machine. All you have
to do is to create a configuration file in JSON format that contains some
sample data and then you're ready to go (see the test/cfg.json file for
an example configuration file).

Installation
------------

Tumbkit is written in [Python][py] so you need to install Python first.

Tumbkit depends on [Bottle][b] (a fast and simple Python web framework):

    easy_install -U bottle

Download tumbkit.py to your project directory.


Usage
-----

To start the server execute the following command:

    python tumbkit.py [-t tpl] [-c cfg] [-p port]

    -t : path to the template file, defaults to ./tpl.html
    -c : path to the configuration file, defaults to ./cfg.json
    -p : port, defaults to 8080

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
* search pages ('/search/$query' and '/search/$query/page/$pagenr')
* day pages ('/day/$year/$month/$day')
* random page ('/random')

Theme:

* all basic variables (except PostSummary)
* text, link, chat and quote posts
* pagination
* variables for custom pages
* all date variables
* tags and notes on posts
* ...

Not yet:

* reblogged
* followings and likes
* photo, audio, video, answer posts
* group blogs and posts


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
[py]:http://www.python.org/