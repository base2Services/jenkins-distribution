#!/usr/bin/env python3

import click
import yaml
from deepmerge import always_merger

@click.command()
@click.option('--plugins-yaml', required=True, help='default plugins yaml file')
@click.option('--override-yaml', required=True, help='overriding plugins yaml file')
@click.option('--output-yaml', required=True, help='merged plugins yaml file')
def merge(plugins_yaml, override_yaml, output_yaml):
    
    click.echo(f'loading default plugins {plugins_yaml}')
    with open(plugins_yaml) as file:       
        default_plugins = yaml.load(file, Loader=yaml.FullLoader)
    
    click.echo(f'loading overriding plugins {override_yaml}')
    with open(override_yaml) as file:    
        override_plugins = yaml.load(file, Loader=yaml.FullLoader)

    if override_plugins is not None and 'plugins' in override_plugins and override_plugins['plugins']:
        # this checks if the file is empty or the plugins list is empty
        click.echo(f'merging plugins found in {override_yaml} with defaults')
        merged_plugins = always_merger.merge(default_plugins, override_plugins)
    else:
        click.echo(f'no plugins found in {override_yaml}, using defaults')
        merged_plugins = default_plugins

    click.echo(f'writing merged plugins to output file {output_yaml}')
    with open(output_yaml, 'w') as outfile:
        yaml.safe_dump(merged_plugins, outfile)


if __name__ == '__main__':
    merge()