import pulumi

# Load modules that are to be deployed by Pulumi
if pulumi.get_stack() == 'core':
    import core
else:
    import ecs


# TODO: make components
# Ex: https://www.pulumi.com/docs/tutorials/aws/s3-folder-component/
# class ServerlessAPI(pulumi.ComponentResource):
#     def __init__(self, name, opts = None):
#         super().__init__('nuage:api:ServerlessAPI', name, None, opts)
#         bucket = s3.Bucket('test')
#         self.register_outputs({
#             'bucket_name': bucket.name
#         })

