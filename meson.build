project(
    'wordbook',
    version: '0.6.0',
    meson_version: '>= 0.59.0',
    default_options: [ 'warning_level=2',
                     ],
)

i18n = import('i18n')
gnome = import('gnome')
python = import('python')

base_id = 'dev.mufeed.Wordbook'

message('Looking for dependencies')
py_installation = python.find_installation('python3')
if not py_installation.found()
    error('No valid python3 binary found')
else
    message('Found python3 binary')
endif

dependency('gobject-introspection-1.0', version: '>= 1.35.0')
dependency('gtk4', version: '>= 4.6')
dependency('libadwaita-1', version: '>=1.0')
dependency('glib-2.0')
dependency('pygobject-3.0', version: '>= 3.29.1')

glib_compile_resources = find_program('glib-compile-resources', required: true)
glib_compile_schemas = find_program('glib-compile-schemas', required: true)
desktop_file_validate = find_program('desktop-file-validate', required: false)
appstreamcli = find_program('appstreamcli', required: false)

version = meson.project_version()
version_array = version.split('.')
major_version = version_array[0].to_int()
minor_version = version_array[1].to_int()
version_micro = version_array[2].to_int()

prefix = get_option('prefix')
bindir = prefix / get_option('bindir')
localedir = prefix / get_option('localedir')

pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
profile = get_option('profile')
moduledir = join_paths(pkgdatadir, meson.project_name())

if get_option('profile') == 'development'
  profile = 'Devel'
  vcs_tag = run_command('git', 'rev-parse', '--short', 'HEAD').stdout().strip()
  application_id = '@0@.@1@'.format(base_id, profile)
else
  profile = ''
  application_id = base_id
endif

subdir('data')
subdir('wordbook')
subdir('po')

gnome.post_install(
  gtk_update_icon_cache: true,
  glib_compile_schemas: true,
  update_desktop_database: true,
)
