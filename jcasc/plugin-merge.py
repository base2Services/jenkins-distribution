#!/usr/bin/env python3

import click
import yaml
from deepmerge import Merger

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

    plugin_merger = Merger()
    merged_plugins = plugin_merger.merge(default_plugins, override_plugins)

    click.echo(f'writing merged plugins to output file {output_yaml}')
    with open(output_yaml, 'w') as outfile:
        yaml.safe_dump(merged_plugins, outfile)


if __name__ == '__main__':
    merge()