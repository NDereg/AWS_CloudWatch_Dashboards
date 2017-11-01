# -*- coding: utf-8 -*-
"""
CW-Manage-Dashboard

TO DO: None
"""

import json
import os
import copy
import boto3


def main():
    """Main worker"""
    config = import_config()
    dash_template = import_dashboard()
    items = config.get('items')
    envs = config.get('environments')
    for env in envs:
        env_name = env.get('environment')
        aws = config.get('default').get(env_name, 'account').get('account')
        api = filter_ec2(*get_args(items, 'tag1', 'api'), env)
        fe = filter_ec2(*get_args(items, 'tag1', 'fe'), env)
        sql = filter_ec2(*get_args(items, 'tag2', 'sql'), env)
        api_alb = filter_alb(*get_args(items, 'albApi'), env)
        fe_alb = filter_alb(*get_args(items, 'albFe'), env)
        values = compile_values(api, fe, sql, api_alb, fe_alb, items, env, aws)
        metric_values = build_metrics(*get_args(env, 'region'), values)
        dashboard = build_dashboard(dash_template, metric_values)
        put_dashboard(dashboard, env)


def import_config():
    """Import ./data/config.json"""
    with open(os.path.abspath('./data/config.json')) as json_config:
        config_template = json.load(json_config)
    return config_template


def import_dashboard():
    """Import ./data/dashboard.json"""
    with open(os.path.abspath('./data/dashboard.json')) as json_dashboard:
        dash_template = json.load(json_dashboard)
    return dash_template


def get_args(source, *args):
    """Get passed in arguments"""
    values = []
    for arg in args:
        values.append(source.get(arg))
    return tuple(values)


def filter_ec2(tagName, ec2Name, env):
    """Filter EC2 Instances by Tag"""
    ec2_list = []
    ec2 = boto3.client('ec2', region_name=env.get('region'))
    instances = ec2.describe_instances(
        Filters=[
            {
                'Name': tagName,
                'Values': [ec2Name]
            }
        ]
    )
    for reservation in instances.get('Reservations'):
        for instance in reservation.get('Instances'):
            ec2_list.append(instance)
    return ec2_list


def build_ec2_metrics(instances):
    """Build EC2 CPU Utilization metrics"""
    metrics = []
    for instance in instances:
        metric = ["AWS/EC2", "CPUUtilization",
                  "InstanceId", instance.get('InstanceId')]
        metrics.append(metric)
    return metrics


def build_request_metrics(fe_ec2):
    """Build EC2 Requests Queued metrics"""
    metrics = []
    for instance in fe_ec2:
        metric = ["System/Windows", "RequestsQueued",
                  "InstanceId", instance.get('InstanceId')]
        metrics.append(metric)
    return metrics


def filter_alb(alb_string, env):
    """Filter ALB Target Group"""
    date = []
    elbv2 = boto3.client('elbv2', region_name=env.get('region'))
    response = elbv2.describe_load_balancers()
    for alb in response.get('LoadBalancers'):
        if alb_string in alb.get('LoadBalancerName'):
            alb_time = alb.get('CreatedTime')
            date.append(alb_time)
    sort_oldest = sorted(date, reverse=False)
    for alb in response.get('LoadBalancers'):
        if alb_string in alb.get('LoadBalancerName'):
            if alb.get('CreatedTime') == sort_oldest[0]:
                current_stack = alb
    return current_stack


def compile_values(api, fe, sql, api_alb, fe_alb, items, env, aws):
    """Compile all values"""
    values = {}
    values['api_metrics'] = build_ec2_metrics(api)
    values['fe_metrics'] = build_ec2_metrics(fe)
    values['sql_metrics'] = build_ec2_metrics(sql)
    values['fe_heapbyte_metrics'] = build_fe_heapbyte_metrics(fe)
    values['fe_request_metrics'] = build_request_metrics(fe)
    values['api_tg_metrics'] = build_tg_metrics(
        api_alb, *get_args(items, 'albApi'), env, aws)
    values['fe_tg_metrics'] = build_tg_metrics(
        fe_alb, *get_args(items, 'albFe'), env, aws)
    values['tg_metrics'] = build_avg_metrics(
        values['api_tg_metrics'][0], values['fe_tg_metrics'][0])
    values['memcache_metrics'] = build_memcache_metrics(env)
    return values


def build_tg_metrics(alb_info, alb_string, env, aws):
    """Build Target Group Response Time metrics"""
    alb_env = "loadbalancer/"
    tg_metrics = []
    client = boto3.client('elbv2', region_name=env.get('region'))
    response = client.describe_listeners(
        LoadBalancerArn=alb_info.get('LoadBalancerArn')
    )
    target_group = response.get('Listeners')[0].get(
        'DefaultActions')[0].get('TargetGroupArn')
    tg_arn = target_group.split(aws, 1)[1]
    alb = alb_info.get('LoadBalancerArn')
    alb_arn = alb.split(alb_env, 1)[1]
    if alb_string in alb_arn:
        for region in env.get('tgRegion'):
            metric = ["AWS/ApplicationELB", "TargetResponseTime", "TargetGroup",
                      tg_arn, "LoadBalancer", alb_arn, "AvailabilityZone", region]
            tg_metrics.append(metric)
    return tg_metrics


def build_avg_metrics(api, fe):
    """Build Target Group Average metrics"""
    tg_metrics = []
    albs = api, fe
    for alb in albs:
        metric = ["AWS/ApplicationELB", "TargetResponseTime", "TargetGroup",
                  alb[3], "LoadBalancer", alb[5]]
        tg_metrics.append(metric)
    return tg_metrics


def build_memcache_metrics(env):
    """Build Memcache node metrics"""
    metrics = []
    client = boto3.client('elasticache', region_name=env.get('region'))
    response = client.describe_cache_clusters(
        CacheClusterId=env.get('cluster'),
        ShowCacheNodeInfo=True
    )
    cluster = response['CacheClusters'][0]
    for node in cluster.get('CacheNodes'):
        metric = ["AWS/ElastiCache", "Evictions", "CacheClusterId",
                  env.get('cluster'), "CacheNodeId", node.get('CacheNodeId')]
        metrics.append(metric)
    return metrics


def build_fe_heapbyte_metrics(fe):
    """Build FE Server HeapBytes"""
    metrics = []
    for f in fe:
        metric = ["System/Windows", "ManagedHeapBytes",
                  "InstanceId", f.get('InstanceId')]
        metrics.append(metric)
    return metrics


def build_metrics(region, values):
    """Build"""
    dash_values = {
        'Metric': values,
        'Region': region,
        'TitlePrefix': {
            'us-east-1': 'NA',
            'eu-west-1': 'EU',
            'ap-southeast-2': 'AU'
        }
    }
    return dash_values


def build_dashboard(dash_template, dash_values):
    """build dashboard"""
    widgets = copy.deepcopy(dash_template.get('widgets'))
    for widget in widgets:
        prop = widget.get('properties')
        metric = dash_values.get('Metric')
        area = dash_values.get('TitlePrefix').get(dash_values.get('Region'))
        prop['metrics'] = metric.get(prop.get('metrics'))
        prop['region'] = dash_values.get('Region')
        prop['title'] = '{}-{}'.format(area, prop.get('title'))
    return widgets


def put_dashboard(dashboard, env):
    """Upload dashboard"""
    body = {'widgets': dashboard}
    body_j = json.dumps(body)
    print(body_j)
    cw = boto3.client('cloudwatch')
    cw.put_dashboard(
        DashboardName=env.get('dashboard'),
        DashboardBody=body_j
    )


if __name__ == '__main__':
    # ensures the cwd is root of project
    __WS_DIR__ = os.path.dirname(os.path.realpath(__file__))
    os.chdir('{}/..'.format(__WS_DIR__))
    main()
