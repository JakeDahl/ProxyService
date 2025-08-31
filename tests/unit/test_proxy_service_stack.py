import aws_cdk as core
import aws_cdk.assertions as assertions

from proxy_service.proxy_service_stack import ProxyServiceStack

# example tests. To run these tests, uncomment this file along with the example
# resource in proxy_service/proxy_service_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = ProxyServiceStack(app, "proxy-service")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
