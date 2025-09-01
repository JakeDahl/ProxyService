from aws_cdk import (
    # Duration,
    Stack,
    # aws_sqs as sqs,
)
from constructs import Construct

from proxy_service.constructs.proxy_construct import ProxyConstruct


class ProxyServiceStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here

        pc = ProxyConstruct(self, 'proxy-construct', id_suffix='main')
