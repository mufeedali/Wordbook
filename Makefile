BUILD := _build

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

help:  ## Print the help message.
	@python3 -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

setup:  ## Setup build folder.
	mkdir -p $(BUILD)
	meson setup . $(BUILD)

local:  ## Configure a local build.
	meson configure $(BUILD) -Dprefix=$$(pwd)/$(BUILD)/testdir
	ninja -C $(BUILD) install

develop:  ## Configure a local build with debugging.
	meson configure $(BUILD) -Dprefix=$$(pwd)/$(BUILD)/testdir -Dprofile=development
	ninja -C $(BUILD) install

run:  ## Run the local build.
	ninja -C $(BUILD) run

install:  ## Install system-wide.
	ninja -C $(BUILD) install

clean:  ## Clean build files.
	rm -r $(BUILD)
