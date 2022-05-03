#!/usr/bin/env python3

import os
import shutil
import click
import yaml
import boto3
from pathlib import Path
from botocore.exceptions import ClientError
import requests
from deepmerge import Merger, always_merger

@click.command()
@click.option('--jcasc-yaml', required=True, help='jcasc yaml file to apply to jenkins, if none is supplied the default jcasc yaml is used')
@click.option('--merge/--no-merge', default=True, help='don\'t use the default jcasc yaml file')
@click.option('--s3-bucket', help='jcasc yaml s3 bucket')
@click.option('--s3-prefix', default='jcasc', help='jcasc yaml s3 prefix')
@click.option('--local-jcasc', help='jcasc yaml local path')
@click.option('--jenkins-url', help='jenkins url')
@click.option('--parameters-yaml', help='key-value parameters file to over-ride default config')
def run(jcasc_yaml, merge, s3_bucket, s3_prefix, local_jcasc, jenkins_url, parameters_yaml):
    ref_path = os.environ.get('REF', '.')
    ciinabox_jobs_path = f'{ref_path}/ciinabox-jobs'

    jcasc_reload_token = os.environ.get('JCASC_RELOAD_TOKEN')
    if jenkins_url and not jcasc_reload_token:
        raise click.ClickException('jcasc reload token not provided by environment variable JCASC_RELOAD_TOKEN')

    # If parameters yaml not set, check if default value exists, otherwise set as None
    if not parameters_yaml:
        if file_exists('parameters.yaml'):
            parameters_yaml = 'parameters.yaml'
        else:
            parameters_yaml =  None

    # load job override parameters and merge with defaults
    job_overrides = read_yaml_file(f'{ref_path}/default-job-overrides.yaml')
    if parameters_yaml:
        supplied_job_overrides = read_yaml_file(parameters_yaml)
        job_overrides = always_merger.merge(job_overrides, supplied_job_overrides)

    print(job_overrides)

    # load default jobs as a string and add to jcasc jobs
    default_jobs = Path(f'{ciinabox_jobs_path}/default.groovy').read_text()
    click.echo("adding default jobdsl jobs to jcasc")
    add_jobs_to_jcasc(jcasc_yaml, default_jobs)

    # setup jenkmon jobs
    jenkmon(f'{ciinabox_jobs_path}/jenkmon.groovy', job_overrides, jcasc_yaml)

    # merge jcasc yamls
    if merge:
        click.echo(f"merging jcasc yaml {jcasc_yaml} with defaults")
        jcasc_yaml = merger(ref_path, jcasc_yaml)

    # deploy jcasc yaml to either s3 or local file system
    if s3_bucket:
        s3_path = f'{s3_prefix}/jenkins.yaml'
        click.echo(f"backing up jcasc yaml in s3 bucket {s3_bucket}/{s3_path}")
        s3_copy(s3_bucket, s3_path, f'{s3_path}.bak')
        click.echo(f"uploading jcasc yaml to s3 bucket {s3_bucket}/{s3_path}")
        s3_upload(s3_bucket, s3_path, jcasc_yaml)
    elif local_jcasc:
        click.echo(f"backing up local jcasc file {local_jcasc}  to {local_jcasc}.bak")
        local_copy(local_jcasc, f'{local_jcasc}.bak')
        click.echo(f"copying jcasc yaml to local file {local_jcasc}")
        local_copy(jcasc_yaml, local_jcasc)

    # reload jenkins to apply the jcasc yaml
    if jenkins_url:
        click.echo(f'reloading jcasc for Jenkins {jenkins_url}')
        reloaded = reload_jcasc(jenkins_url, jcasc_reload_token)

        if not reloaded:
            click.echo('attempting to rollback jcasc changes ...')

            if s3_bucket:
                s3_path = f'{s3_prefix}/jenkins.yaml'
                click.echo(f"rolling back jcasc yaml in s3 bucket {s3_bucket}/{s3_path}")
                s3_copy(s3_bucket, f'{s3_path}.bak', s3_path)
            elif local_jcasc:
                click.echo(f"rolling back local backup jcasc file {local_jcasc}.bak to {local_jcasc}")
                local_copy(f'{local_jcasc}.bak', local_jcasc)

            raise click.ClickException('failed to reload jcasc, check jenkins logs for more details')

        click.echo(f'jcasc config has been reloaded')


def str_presenter(dumper, data):
    """format multiline strings neatly in the yaml dumper"""
    if len(data.splitlines()) > 1:  # check for multiline string
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)


def jcasc_dict_merge(config, path, base, nxt):
    """
    if keys match particular jcasc keys that cannot be merged then override
    for keys that do not exists, use them directly. 
    if the key exists in both dictionaries, attempt a value merge.
    """
    for k, v in nxt.items():
        # keys where a single entry map is expected
        if k in ['authorizationStrategy', 'securityRealm']:
            base[k] = v
        elif k not in base:
            base[k] = v
        else:
            base[k] = config.value_strategy(path + [k], base[k], v)
    return base


def merger(ref_path, overriding_jcasc_yaml):
    # load the jcasc defaults bundles int he docker image
    with open(f'{ref_path}/defaults.yaml') as file:       
        default_jcasc = yaml.load(file, Loader=yaml.FullLoader)
    
    # load the user supplied jcasc
    with open(overriding_jcasc_yaml) as file:       
        overriding_jcasc = yaml.load(file, Loader=yaml.FullLoader)

    # set up the merger with the merge strategies
    jcasc_merger = Merger(
        [
            (list, ["override"]),
            (dict, [jcasc_dict_merge]),
            (set, ["union"])
        ],
        # fallback strategy
        ["override"],
        # conflict strategy
        ["override"]
    )

    merged = jcasc_merger.merge(default_jcasc, overriding_jcasc)

    merged_jcasc = f'{ref_path}/jenkins.yaml'

    # write our merged jcasc yaml
    write_yaml_file(merged_jcasc, merged)

    return merged_jcasc


def s3_copy(bucket_name, path_copy_from, path_copy_to):
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(bucket_name)
    newobj = bucket.Object(path_copy_to)
    try:
        newobj.copy({'Bucket': bucket_name, 'Key': path_copy_from})
    except ClientError as ex:
        if 'Not Found' in ex.response['Error']['Message']:
            click.echo(f'unable to copy s3 file {path_copy_from} as file doesn\'t exist in bucket {bucket}')
        else:
            raise

def s3_upload(bucket, path, jcasc_yaml):
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(bucket)
    bucket.upload_file(jcasc_yaml, path)


def local_copy(jcasc_yaml, path):
    shutil.copy(jcasc_yaml, path)


def reload_jcasc(jenkins_url, jcasc_reload_token):
    response = requests.post(f"{jenkins_url}/reload-configuration-as-code/?casc-reload-token={jcasc_reload_token}")
    if response.status_code == 403:
        click.echo(f"failed to authenticate to jenkins, check JCASC_RELOAD_TOKEN env var is set on your Jenkins instance.", err=True)
        return False
    elif response.status_code != 200:
        click.echo(f'failed to reload jenkins jcasc via the jcasc reload url /reload-configuration-as-code/?casc-reload-token=**** with status code {response.status_code}', err=True)
        return False
    return True

def read_yaml_file(file_name):
    with open(file_name, 'r') as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
            return {}

def write_yaml_file(file_name, contents):
    yaml.add_representer(str, str_presenter, Dumper=yaml.SafeDumper)
    with open(file_name, 'w') as outfile:
        yaml.safe_dump(contents, outfile, default_flow_style=False)

def add_jobs_to_jcasc(jcasc_yaml, jobs):
    current_jcasc = read_yaml_file(jcasc_yaml)

    script_dict = {'script': jobs}
    if 'jobs' in current_jcasc.keys():
        current_jcasc['jobs'].append(script_dict)
    else:
        current_jcasc['jobs'] = [script_dict]
    write_yaml_file(jcasc_yaml, current_jcasc)

def jenkmon(jenkmon_job_template_path, job_overrides, jcasc_yaml):
    """
    load jenkmon job template and override values specified in the job overrides
    """
    jenkmon_job_template = Path(jenkmon_job_template_path).read_text()
    for name, overrides in job_overrides['jenkmon'].items():
        jenkmon_job = jenkmon_job_template
        for key, value in overrides.items():
            jenkmon_job = jenkmon_job.replace(f"{{{{{key.upper()}}}}}", value)
        click.echo(f"adding {name} jenkmon job to jcasc")
        add_jobs_to_jcasc(jcasc_yaml, jenkmon_job)

def file_exists(file_name):
    return os.path.isfile(file_name)


if __name__ == '__main__':
    run()