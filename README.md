# Revoko

![GitHub](https://img.shields.io/github/license/aewens/revoko?style=for-the-badge))]

## Overview
A self-hosted service used to store and recall personal data. The name comes from Esperanto for the word "recall", given its intended functionality. The project has a strong focus on modularity to allow for various components to be easily swapped out later on, and as such needs a way to orchestrate and compose its various components together to create a cohesive and unified application. That is the purpose that this specific repository serves in the project as it will facilitate:

- [ ] Distributing a single configuration file to be shared across the other components to reduce duplication
- [ ] Providing a daemon to run the service from a single entry point
- [ ] Automatically update components when new changes are made available in the master branch of their repositories

The goal for accomplishing those features is to provide a plugin system for the daemon to execute any scripts needed to build/setup/run the various components and dictate how they should be structured together to interact properly. To assist in the separation of concerns, the daemon will only have the plugin engine and knowledge of where to search for these scripts, but will not hold any of them itself (i.e. these scripts will need to be listed in their respective repositories). This process will follow the execution order:

1. Read the configuration file to extract which components will be utilitzed
1. Check to see if any of the components are missing, and if so clone them into the components directory
1. Check to see if any of the components have any new commits on their master branch, and if so pull in the new changes
1. Start the daemon(s) by running any scripts provided by the components (this will be where the components can request the shared configuration file)
1. When the stopping the daemon(s) it will run any cleanup scripts provided by the components after sending SIGTERM to their process(es) 

Since the components can have more than one script to run, for multiple scripts by convention using a number to prefix the script name (e.g. 00_initialize.sh) will ensure they all execute in the expected order. The shared configuration file will dictate the order the components are run in case any need to be run before or after another component to work properly.
