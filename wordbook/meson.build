pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
moduledir = join_paths(pkgdatadir, 'wordbook')

python = import('python')

conf = configuration_data()
conf.set_quoted('PROFILE', profile)
conf.set('PYTHON', python.find_installation('python3').path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', join_paths(get_option('prefix'), get_option('localedir')))
conf.set('pkgdatadir', pkgdatadir)
conf.set('datadir', get_option('datadir'))
conf.set('prefix', get_option('prefix'))

configure_file(
  input: 'wordbook.in',
  output: 'wordbook',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir')
)

myprogram = join_paths(meson.build_root(), meson.project_name(), meson.project_name())
run_target('run',
  command: [myprogram]
)

wordbook_sources = [
  '__init__.py',
  'base.py',
  'main.py',
  'settings.py',
  'settings_window.py',
  'utils.py',
  'window.py',
]

install_data(wordbook_sources, install_dir: moduledir)
