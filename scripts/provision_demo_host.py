"""Provision only the dedicated MCP Kart private operator host; no shared network changes."""
import hashlib
import json
import tarfile
import time
from pathlib import Path

import boto3
from botocore.config import Config

ROOT = Path(__file__).resolve().parents[1]
PREFIX = 'mcpkart-aws-demo-20261029'
OUT = ROOT / 'artifacts/aws-demo-ec2-v1'


def main():
    OUT.mkdir(exist_ok=False)
    plan = json.loads((ROOT/'artifacts/aws-demo-ec2-plan.json').read_text())
    own = json.loads((ROOT/'artifacts/aws-demo-package-v3/aws-resources.json').read_text())['resources']
    release = ROOT/'artifacts/aws-demo-dnf-release-v2'
    cfg = Config(retries={'total_max_attempts': 1})
    session = boto3.Session(region_name=plan['region'])
    assert session.client('sts', config=cfg).get_caller_identity()['Account'] == plan['account']
    state = {'account': plan['account'], 'region': plan['region'], 'prefix': PREFIX, 'resources': {}}

    def save(kind, value):
        state['resources'][kind] = value
        (OUT/'resources.json').write_text(json.dumps(state, indent=2))

    secrets = session.client('secretsmanager', config=cfg)
    private = json.loads((ROOT/'artifacts/aws-demo-temporal-private.json').read_text())
    secret = secrets.create_secret(Name=PREFIX+'/temporal', SecretString=json.dumps(private),
                                   Tags=[{'Key': 'Project', 'Value': 'MCPKart'}])['ARN']
    save('temporal_secret', secret)
    archive = OUT/'source.tar.gz'
    with tarfile.open(archive, 'w:gz') as target:
        paths = [ROOT/'pyproject.toml', ROOT/'uv.lock']
        paths += [p for p in (ROOT/'src').rglob('*') if p.is_file() and '__pycache__' not in p.parts]
        paths += [ROOT/'scripts/export_duel_replay.py']
        for path in paths:
            target.add(path, arcname=str(path.relative_to(ROOT)), recursive=False)
        for name in ('release.json', 'deployment.json'):
            target.add(release/name, arcname='artifacts/aws-demo-dnf-release-v2/'+name)
        target.add(ROOT/'artifacts/budget.json', arcname='artifacts/budget.json')
    key = 'operator/source-'+hashlib.sha256(archive.read_bytes()).hexdigest()+'.tar.gz'
    s3 = session.client('s3', config=cfg)
    s3.upload_file(str(archive), own['bucket'], key)
    save('bucket', own['bucket']); save('source_key', key)
    iam = session.client('iam', config=cfg)
    role_name = PREFIX+'-operator'
    role = iam.create_role(RoleName=role_name, AssumeRolePolicyDocument=json.dumps({
        'Version': '2012-10-17', 'Statement': [{'Effect': 'Allow', 'Principal': {'Service': 'ec2.amazonaws.com'},
                                              'Action': 'sts:AssumeRole'}]}),
        Tags=[{'Key': 'Project', 'Value': 'MCPKart'}])['Role']['Arn']
    save('role', role)
    iam.attach_role_policy(RoleName=role_name, PolicyArn='arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore')
    iam.put_role_policy(RoleName=role_name, PolicyName=PREFIX, PolicyDocument=json.dumps({
        'Version': '2012-10-17', 'Statement': [
            {'Effect': 'Allow', 'Action': ['s3:GetObject', 's3:PutObject'],
             'Resource': 'arn:aws:s3:::'+own['bucket']+'/operator/*'},
            {'Effect': 'Allow', 'Action': 's3:ListBucket', 'Resource': 'arn:aws:s3:::'+own['bucket'],
             'Condition': {'StringLike': {'s3:prefix': 'operator/*'}}},
            {'Effect': 'Allow', 'Action': 'secretsmanager:GetSecretValue', 'Resource': secret},
            {'Effect': 'Allow', 'Action': ['bedrock-agentcore:InvokeAgentRuntime', 'bedrock-agentcore:GetAgentRuntime'],
             'Resource': [own['runtime'], own['runtime']+'/*']},
        ]}))
    iam.create_instance_profile(InstanceProfileName=role_name)
    iam.add_role_to_instance_profile(InstanceProfileName=role_name, RoleName=role_name)
    save('instance_profile', role_name)
    ec2 = session.client('ec2', config=cfg)
    tags = [{'Key': 'Project', 'Value': 'MCPKart'}, {'Key': 'Name', 'Value': PREFIX+'-operator'}]
    vpc = ec2.create_vpc(CidrBlock='10.88.0.0/24', TagSpecifications=[{'ResourceType': 'vpc', 'Tags': tags}])['Vpc']['VpcId']
    save('vpc', vpc)
    ec2.modify_vpc_attribute(VpcId=vpc, EnableDnsSupport={'Value': True})
    subnet = ec2.create_subnet(VpcId=vpc, CidrBlock='10.88.0.0/26', TagSpecifications=[{'ResourceType': 'subnet', 'Tags': tags}])['Subnet']['SubnetId']
    save('subnet', subnet)
    gateway = ec2.create_internet_gateway(TagSpecifications=[{'ResourceType': 'internet-gateway', 'Tags': tags}])['InternetGateway']['InternetGatewayId']
    save('internet_gateway', gateway); ec2.attach_internet_gateway(InternetGatewayId=gateway, VpcId=vpc)
    table = ec2.create_route_table(VpcId=vpc, TagSpecifications=[{'ResourceType': 'route-table', 'Tags': tags}])['RouteTable']['RouteTableId']
    save('route_table', table)
    ec2.create_route(RouteTableId=table, DestinationCidrBlock='0.0.0.0/0', GatewayId=gateway)
    association = ec2.associate_route_table(RouteTableId=table, SubnetId=subnet)['AssociationId']; save('route_association', association)
    group = ec2.create_security_group(GroupName=PREFIX+'-operator', Description='MCP Kart outbound-only operator; SSM access', VpcId=vpc)['GroupId']
    save('security_group', group)  # No ingress rules are added.
    user_data = f'''#!/bin/bash
set -eu
umask 077
dnf install -y docker
command -v aws
systemctl enable --now docker
mkdir -p /opt/mcpkart
aws s3 cp s3://{own['bucket']}/{key} /tmp/mcpkart-source.tar.gz --region us-west-2
tar -xzf /tmp/mcpkart-source.tar.gz -C /opt/mcpkart
cd /opt/mcpkart
mkdir -p artifacts/aws-demo-free-v1 image
aws secretsmanager get-secret-value --region us-west-2 --secret-id {secret} --query SecretString --output text > artifacts/aws-demo-temporal-private.json
cp pyproject.toml uv.lock image/
cat > image/Dockerfile <<'EOF'
FROM python:3.14.8-slim
RUN pip install --no-cache-dir uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --extra demo --dev --no-install-project --python /usr/local/bin/python
ENV PATH="/app/.venv/bin:$PATH"
EOF
docker build -t mcpkart-demo-linux:host image
docker run -d --name mcpkart-demo --network host --mount type=bind,src=/opt/mcpkart,dst=/workspace,readonly --mount type=bind,src=/opt/mcpkart/artifacts,dst=/workspace/artifacts --workdir /workspace --env PYTHONPATH=/workspace/src --env PYTHONDONTWRITEBYTECODE=1 --env AWS_DEFAULT_REGION=us-west-2 mcpkart-demo-linux:host sleep infinity
docker exec -d mcpkart-demo python -m mcpkart.duel_web --trio --watchdog --host 127.0.0.1 --port 8771 --replay-root artifacts/aws-demo-free-v1
printf 'ready\\n' > artifacts/host-ready
'''
    (OUT/'bootstrap.sh').write_text(user_data)  # Contains ARNs/paths only, no secrets.
    time.sleep(12)  # IAM profile propagation, no model request or infrastructure retry.
    instance = ec2.run_instances(ImageId=plan['ami'], InstanceType='m7g.large', MinCount=1, MaxCount=1,
        ClientToken=PREFIX+'-operator-v1', IamInstanceProfile={'Name': role_name}, UserData=user_data,
        NetworkInterfaces=[{'DeviceIndex': 0, 'SubnetId': subnet, 'Groups': [group], 'AssociatePublicIpAddress': True}],
        MetadataOptions={'HttpTokens': 'required', 'HttpPutResponseHopLimit': 2},
        BlockDeviceMappings=[{'DeviceName': '/dev/xvda', 'Ebs': {'VolumeSize': 24, 'VolumeType': 'gp3', 'Encrypted': True, 'DeleteOnTermination': True}}],
        TagSpecifications=[{'ResourceType': 'instance', 'Tags': tags}, {'ResourceType': 'volume', 'Tags': tags}])['Instances'][0]
    save('instance', instance['InstanceId'])
    print(json.dumps({'instance': instance['InstanceId'], 'ingress_rules': 0, 'existing_resources_modified': False}), flush=True)


if __name__ == '__main__':
    main()
