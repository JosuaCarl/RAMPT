#!/usr/bin/bash
PROJECTFILE=$1

# Update tag from pyproject.toml
get_toml_value() {
    # Takes three parameters:
    # - TOML file path ($1)
    # - section ($2)
    # - the key ($3)
    # 
    # It first gets the section using the get_section function
    # Then it finds the key within that section
    # using grep and cut.

    local file="$PROJECTFILE"
    local section="project"
    local key="version"

    get_section() {
        # Function to get the section from a TOML file
        # Takes two parameters:
        # - TOML file path ($1)
        # - section name ($2)
        # 
        # It uses sed to find the section
        # A section is terminated by a line with [ in pos 0 or the end of file.

        local file="$1"
        local section="$2"

        sed -n "/^\[$section\]/,/^\[/p" "$file" | sed '$d'
    }
        
    get_section "$file" "$section" | grep "^$key " | cut -d "=" -f2- | tr -d ' "'
}  
# End Function get_toml_value()

# Tag the current version
VERSION="v$(get_toml_value)"

if grep -q "$VERSION" <<< "$(git tag -l | cat)"; then
  echo "Already tagged with this version"
else
  echo "Tagging this as new version"
  git tag -a $VERSION -m "Tagged new version"
  git push --tags
fi
