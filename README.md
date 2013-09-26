PasteCookie
===========

PasteCookie is the source code of [daimaduan.com](http://daimaduan.com). It is open sourced under new BSD license.

## How to install it?

*You need to use `virtualenv` to run it*

1. `virtualenv venv --python python2.7`
2. `pip install -r requirements.txt`
3. `cd website`
4. `cp config.cfg.sample test.cfg`
5. Edit it according to your ENV
6. `python manage.py initdb --config test.cfg`
7. `python manage.py run --config test.cfg`
8. Visit http://127.0.0.1:5000/ in your favourite browser

## Troubleshooting

### Error: pg\_config executable not found.

`pg_config` is in postgresql-devel (libpq-dev in Debian/Ubuntu)

    $ sudo apt-get install libpq-dev

via: http://stackoverflow.com/a/12037133/260793

## How to submit my idea?

Create an issue on Github

## How to contribute?

1. fork this project
2. create your own feature branch
3. write your code
4. commit it and push it to Github
5. create a pull-request on Github

