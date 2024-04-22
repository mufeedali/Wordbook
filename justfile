BUILD := "_build"

default:
  @just --choose

# Setup build folder.
setup:
	mkdir -p {{BUILD}}
	meson setup . {{BUILD}}

# Configure a local build.
local-configure:
	meson configure {{BUILD}} -Dprefix=$(pwd)/{{BUILD}}/testdir
	ninja -C {{BUILD}} install

# Configure a local build with debugging.
develop-configure:
	meson configure {{BUILD}} -Dprefix=$(pwd)/{{BUILD}}/testdir -Dprofile=development
	ninja -C {{BUILD}} install

# Run the local build.
local-run:
	ninja -C {{BUILD}} run

# Install system-wide.
install:
	ninja -C {{BUILD}} install

# Clean build files.
clean:
	rm -r {{BUILD}}

# Do everything needed and then run Wordbook for develpment in one command.
run: setup develop-configure local-run clean