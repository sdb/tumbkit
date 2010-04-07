Tumbkit
=======

Tumbkit is a toolkit to facilitate [Tumblr][t] theme development. This is still
a work in progress and at the moment not all functionality is implemented.


Usage
-----

Tumbkit offers a server which renders your custom Tumblr template (theme).
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
