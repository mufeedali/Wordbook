message('Installing icons')

# Scalable
icondir = join_paths(get_option('datadir'), 'icons/hicolor/scalable/apps')
install_data (
    application_id + '.svg',
    install_dir: icondir
)

# Symbolic
icondir = join_paths(get_option('datadir'), 'icons/hicolor/symbolic/apps')
install_data (
    base_id + '-symbolic.svg',
    install_dir: icondir
)

