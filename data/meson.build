subdir('icons')
subdir('resources')

if get_option('install_wn_db')
  custom_target('wn-db',
    output: 'wn-@0@.db.zst'.format(wn_version),
    command: [
      find_program('python3'),
      join_paths(meson.project_source_root(), 'scripts', 'generate-wn-db.py'),
      '--output', '@OUTPUT@'
    ],
    install: true,
    install_dir: pkgdatadir,
    console: true,
  )
endif

# Desktop file
desktop_conf = configuration_data()
desktop_conf.set('app-id', application_id)
desktop_file = i18n.merge_file(
  input: configure_file(
    input: '@0@.desktop.in.in'.format(base_id),
    output: '@BASENAME@',
    configuration: desktop_conf
  ),
  output: '@0@.desktop'.format(application_id),
  type: 'desktop',
  po_dir: '../po',
  install: true,
  install_dir: join_paths(get_option('datadir'), 'applications')
)

desktop_utils = find_program('desktop-file-validate', required: false)
if desktop_utils.found()
  test('Validate desktop file', desktop_utils,
    args: [desktop_file.full_path()]
  )
endif

# Metainfo file
appdata_conf = configuration_data()
appdata_conf.set('app-id', application_id)
appstream_file = i18n.merge_file(
  input: configure_file(
    input: '@0@.metainfo.xml.in.in'.format(base_id),
    output: '@BASENAME@',
    configuration: appdata_conf
  ),
  output: '@0@.metainfo.xml'.format(application_id),
  po_dir: '../po',
  install: true,
  install_dir: join_paths(get_option('datadir'), 'metainfo')
)

appstreamcli = find_program('appstreamcli', required: false)
if appstreamcli.found()
  test('Validate appstream file', appstreamcli,
    args: ['validate', '--no-net', appstream_file.full_path()]
  )
endif

# GSettings schema
gschema_conf = configuration_data()
gschema_conf.set('app-id', application_id)
configure_file(
  input: '@0@.gschema.xml.in'.format(base_id),
  output: '@0@.gschema.xml'.format(application_id),
  configuration: gschema_conf,
  install: true,
  install_dir: join_paths(get_option('datadir'), 'glib-2.0/schemas')
)

compile_schemas = find_program('glib-compile-schemas', required: false)
if compile_schemas.found()
  test('Validate schema file', compile_schemas,
    args: ['--strict', '--dry-run', meson.current_source_dir()]
  )
endif

conf = configuration_data()

conf.set('APP_ID', application_id)
conf.set('PYTHON', python.find_installation('python3').full_path())
conf.set('localedir', join_paths(get_option('prefix'), get_option('localedir')))
conf.set('pkgdatadir', pkgdatadir)
conf.set('BIN', join_paths(get_option('prefix'), get_option('bindir'), meson.project_name()))

if get_option('profile') == 'development'
  object_path = '/dev/mufeed/Wordbook/Devel/SearchProvider'
else
  object_path = '/dev/mufeed/Wordbook/SearchProvider'
endif
object_path
conf.set('object_path', object_path)

search_provider_dir = join_paths(get_option('prefix'), get_option('datadir'), 'gnome-shell', 'search-providers')
service_dir = join_paths(get_option('prefix'), get_option('datadir'), 'dbus-1', 'services')

configure_file(
  input: '@0@.SearchProvider.ini'.format(base_id),
  output: '@0@.SearchProvider.ini'.format(application_id),
  configuration: conf,
  install_dir: search_provider_dir,
)

configure_file(
  input: '@0@.SearchProvider.service.in'.format(base_id),
  output: '@0@.SearchProvider.service'.format(application_id),
  configuration: conf,
  install_dir: service_dir,
)

configure_file(
  input: 'search_provider.in',
  output: 'search_provider',
  configuration: conf,
  install_dir: pkgdatadir,
)
