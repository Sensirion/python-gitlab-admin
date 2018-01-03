#!/usr/bin/python2
# vim: set fileencoding=utf-8
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
"""GitLab provisioning script
Usage:
    gitlab_admin [(-v ...)] [options]
    gitlab_admin (-h | --help)

Options:
    -h --help                    Show this help screen.
    --dry-run                    Do not change anything
    -s, --server GITLAB_SERVER   GitLab server to choose from config file
    -t, --token GITLAB_TOKEN     GitLab access token
    -g, --group GITLAB_GROUP     GitLab group to work on
    --host GITLAB_HOST           GitLab hostname
    -c, --config CONFIG_FILE     configuration file [default: config.toml]
    -v, --verbose                Enable debug messages, may be passed multiple times
"""

from __future__ import absolute_import, division, print_function, unicode_literals
import os
import logging
from logging import debug, info

import gitlab
import toml
from docoptcfg import docoptcfg


SSL_VERIFY = os.environ.get('REQUESTS_CA_BUNDLE', True)


def apply_protected_branches(project, protected_branches, dry_run):
    protected_branches_list = project.protectedbranches.list()
    for protected_branch in protected_branches:
        branch = next((x for x in protected_branches_list if x.name == protected_branch['name']), None)
        if branch is None:
            debug("protected branch {} does not exists".format(protected_branch['name']))
        else:
            debug("protected branch exists: {}".format(branch))
            attributes = branch.attributes
            if (len(attributes['merge_access_levels']) == 1 and
                    attributes['merge_access_levels'][0]['access_level'] == protected_branch['merge_access_level'] and
                    len(attributes['push_access_levels']) == 1 and
                    attributes['push_access_levels'][0]['access_level'] == protected_branch['push_access_level']):
                debug("settings are equal")
                continue
            if not dry_run:
                # need to remove first to change settings
                info("Remove branch protection for {}".format(protected_branch['name']))
                project.protectedbranches.delete(protected_branch['name'])
        print("{}: change: protect branch: {}".format(project.path_with_namespace, protected_branch['name']))
        debug("{}".format(protected_branch))
        if not dry_run:
            project.protectedbranches.create(
                    {'name': protected_branch['name']},
                    push_access_level=protected_branch['push_access_level'],
                    merge_access_level=protected_branch['merge_access_level'])


def apply_rules(project, config, dry_run=True):
    rules = config['rules']
    if rules.get('protected-branches'):
        apply_protected_branches(project, rules['protected-branches'], dry_run)


def recurse_subgroups(all_groups, group):
    """
    Given a list of all groups on a GitLab server, recursively extracts all
    subgroups of a given group
    """
    sub_groups = []
    for sub_group in [sub_group for sub_group in all_groups if sub_group.parent_id == group.id]:
        sub_groups.append(sub_group)
        recurse_subgroups(all_groups, sub_group)

    return sub_groups


def main():
    arguments = docoptcfg(__doc__, env_prefix='GITLAB_')
    gitlab_token = arguments.get('--token')
    gitlab_group = arguments.get('--group')
    gitlab_config = arguments.get('--config')
    gitlab_host = arguments.get('--host')
    gitlab_server = arguments.get('--server')
    dry_run = arguments.get('--dry-run')
    verbose = arguments.get('--verbose')
    logging.basicConfig(level=(50 - verbose*10))

    config = toml.load(gitlab_config)

    if gitlab_server is None:
        gitlab_server = config['gitlab_admin']['default_server']
    if gitlab_host is None:
        gitlab_host = config['servers'][gitlab_server]['host']
    if gitlab_token is None:
        gitlab_token = config['servers'][gitlab_server]['token']
    if gitlab_group is None:
        gitlab_group = config['gitlab_admin']['default_group']

    assert gitlab_host, "GITLAB_HOST not defined, export an ENV var or pass command line argument"
    assert gitlab_token, "GITLAB_TOKEN not defined, export an ENV var or pass command line argument"
    assert gitlab_group, "GITLAB_GROUP not defined, export an ENV var or pass command line argument"

    gl = gitlab.Gitlab(gitlab_host, gitlab_token, api_version=4, ssl_verify=SSL_VERIFY)
    group = gl.groups.get(gitlab_group)
    all_groups = gl.groups.list(all=True)
    sub_groups = recurse_subgroups(all_groups, group)

    for sg in sub_groups:
        for project in sg.projects.list():
            apply_rules(project, config)
    for project in group.projects.list():
        apply_rules(project, config, dry_run)


if __name__ == "__main__":
    main()
