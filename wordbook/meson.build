pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
moduledir = join_paths(pkgdatadir, 'wordbook')

python = import('python')

conf = configuration_data()

conf.set_quoted('APP_ID', application_id)
conf.set_quoted('VERSION', meson.project_version())
conf.set_quoted('PROFILE', profile)

conf.set('PYTHON', python.find_installation('python3').full_path())
conf.set_quoted('localedir', join_paths(get_option('prefix'), get_option('localedir')))
conf.set_quoted('pkgdatadir', pkgdatadir)
conf.set('datadir', get_option('datadir'))
conf.set('prefix', get_option('prefix'))
conf.set('WN_FILE_VERSION', wn_version)

configure_file(
  input: 'wordbook.in',
  output: 'wordbook',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir')
)

configure_file(
  input: 'constants.py',
  output: 'constants.py',
  configuration: conf,
  install: true,
  install_dir: moduledir
)

program_executable = join_paths(
  meson.project_build_root(),
  meson.project_name(),
  meson.project_name()
)
run_target('run',
  command: [program_executable]
)

wordbook_sources = [
  '__init__.py',
  'base.py',
  'database.py',
  'main.py',
  'settings.py',
  'settings_window.py',
  'utils.py',
  'window.py',
]

install_data(wordbook_sources, install_dir: moduledir)

install_subdir(
  join_paths(meson.project_source_root(), 'subprojects/wn/wn'),
  install_dir: pkgdatadir,
  exclude_directories: ['__pycache__']
)
