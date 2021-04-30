project('wordbook',  
          version: '0.3.0',
    meson_version: '>= 0.50.0',
  default_options: [ 'warning_level=2',
                   ],
)

app_id = 'com.github.fushinari.Wordbook'

python = import('python')

pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
profile = get_option('profile')
moduledir = join_paths(pkgdatadir, meson.project_name())

message('Looking for dependencies')
py_installation = python.find_installation('python3')
if not py_installation.found()
    error('No valid python3 binary found')
else
    message('Found python3 binary')
endif

dependency('gobject-introspection-1.0', version: '>= 1.35.0')
dependency('gtk+-3.0', version: '>= 3.22')
dependency('glib-2.0')
dependency('pygobject-3.0', version: '>= 3.29.1')

subdir('data')
subdir('wordbook')

meson.add_install_script('build-aux/meson/postinstall.py')
