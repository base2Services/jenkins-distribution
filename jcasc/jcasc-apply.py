#!/usr/bin/env python3

import os
import shutil
import click
import yaml
import boto3
import requests
import base64
from deepmerge import Merger

@click.command()
@click.option('--jcasc-yaml', required=True, help='jcasc yaml file to apply to jenkins, if none is suplied the deafult jcasc yaml is used')
@click.option('--merge/--no-merge', default=True, help='dont use the default jcasc yaml file')
@click.option('--s3-bucket', help='jcasc yaml s3 bucket')
@click.option('--s3-prefix', default='jcasc', help='jcasc yaml s3 prefix')
@click.option('--local-path', help='jcasc yaml local path')
@click.option('--jenkins-url', help='jenkins url')
def run(jcasc_yaml, merge, s3_bucket, s3_prefix, local_path, jenkins_url):
    ref_path = os.environ.get('REF', '.')

    if merge:
        click.echo(f"merging jcasc yaml {jcasc_yaml} with defaults")
        jcasc_yaml = merger(ref_path, jcasc_yaml)

    if s3_bucket:
        s3_path = f'{s3_prefix}/jenkins.yaml'
        click.echo(f"uploading jcasc yaml to s3 bucket {s3_bucket}/{s3_path}")
        s3_upload(s3_bucket, s3_path, jcasc_yaml)
    elif local_path:
        click.echo(f"copying jcasc yaml to local path {local_path}")
        local_copy(local_path, jcasc_yaml)

    if jenkins_url:
        click.echo(f'releading jcasc for Jenkins {jenkins_url}')
        reload_jcasc(jenkins_url)
        click.echo(f'jcasc config has been releaded')


def str_presenter(dumper, data):
    """format multiline strings neatly in the yaml dummper"""
    if len(data.splitlines()) > 1:  # check for multiline string
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)


def merger(ref_path, overriding_jcasc_yaml):
    with open(f'{ref_path}/defaults.yaml') as file:       
        default_jcasc = yaml.load(file, Loader=yaml.FullLoader)

    with open(overriding_jcasc_yaml) as file:       
        overriding_jcasc = yaml.load(file, Loader=yaml.FullLoader)

    jcasc_merger = Merger(
        [
            (list, ["override"]),
            (dict, ["merge"]),
            (set, ["union"])
        ],
        ["override"],
        ["override"]
    )

    merged = jcasc_merger.merge(default_jcasc, overriding_jcasc)

    yaml.add_representer(str, str_presenter)

    merged_jacsc = f'{ref_path}/jenkins.yaml'

    with open(merged_jacsc, 'w') as outfile:
        yaml.dump(merged, outfile, default_flow_style=False)

    return merged_jacsc


def s3_upload(bucket, path, jcasc_yaml):
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(bucket)
    bucket.upload_file(jcasc_yaml, path)


def local_copy(path, jcasc_yaml):
    shutil.copy(jcasc_yaml, path)

def reload_jcasc(jenkins_url):
    jenkins_api_key = os.environ.get('JENKINS_API_KEY')
    jenkins_username = os.environ.get('JENKINS_USERNAME')

    if not jenkins_api_key or not jenkins_username:
        raise click.ClickException('one or more environemnt variables of JENKINS_API_KEY, JENKINS_USERNAME are not set')

    auth = base64.b64encode(f"{jenkins_username}:{jenkins_api_key}".encode('ascii')).decode('ascii')
    url = f"{jenkins_url}/configuration-as-code/reload"
    response = requests.post(url, headers={'Authorization': f'Basic {auth}'})

    if response.status_code != 200:
        raise click.ClickException(f'failed to reload jenkins jcasc via the jcasc reload url /configuration-as-code/reload')

if __name__ == '__main__':
    run()