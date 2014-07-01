from django.contrib.auth.models import User, Group
from rest_framework import serializers
from taxii.models import Inbox, DataFeed, MessageBindingId, ContentBindingId, ContentBlock, ProtocolBindingId, DataFeedPushMethod, DataFeedPollInformation, DataFeedSubscriptionMethod, DataFeedSubscription, ContentBlockRTIR, Services, ServerServices

class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'username', 'email', 'groups')

class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ('url', 'name')

class ProtocolBindingIdSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ProtocolBindingId
        fields = ('title', 'description', 'binding_id', 'date_created', 'date_updated')

class ContentBindingIdSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ContentBindingId
        fields = ('id', 'title', 'description', 'binding_id', 'date_created', 'date_updated')

class MessageBindingIdSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = MessageBindingId
        fields = ('title', 'description', 'binding_id', 'date_created', 'date_updated')

class DataFeedPushMethodSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = DataFeedPushMethod
        fields = ('title', 'description', 'protocol_binding', 'message_binding', 'date_created', 'date_updated')

class DataFeedPollInformationSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = DataFeedPollInformation
        fields = ('id', 'title', 'description', 'address', 'protocol_binding', 'message_bindings', 'date_created', 'date_updated')

class DataFeedSubscriptionMethodSerializer(serializers.HyperlinkedModelSerializer):
  class Meta:
        model = DataFeedSubscriptionMethod
        fields = ('title', 'description', 'address', 'protocol_binding', 'message_bindings', 'date_created', 'date_updated')

class ContentBlockSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ContentBlock
        fields = ('id', 'title', 'description', 'timestamp_label', 'submitted_by', 'message_id', 'content_binding', 'content', 'padding', 'date_created', 'date_updated')

class DataFeedSerializer(serializers.HyperlinkedModelSerializer):
    subscription_methods = serializers.RelatedField(many=True)
    class Meta:
        model = DataFeed
        fields = ('id', 'name', 'description', 'users', 'supported_content_bindings', 'push_methods', 'poll_service_instances', 'subscription_methods', 'content_blocks', 'date_created', 'date_updated')

class DataFeedSubscriptionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = DataFeedSubscription
        fields = ('subscription_id', 'user', 'data_feed', 'data_feed_method', 'active', 'expires', 'date_created', 'date_updated')

class InboxSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Inbox
        fields = ('name', 'description', 'supported_content_bindings', 'supported_message_bindings', 'content_blocks', 'supported_protocol_binding', 'data_feeds', 'users', 'date_created', 'date_updated')

class ContentBlockRTIRSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ContentBlockRTIR
        fields = ('rtir_id', 'content_block')


class ServicesSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Services
        fields = ('id', 'name', 'service_type', 'service_ext')

class ServerServicesSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ServerServices
        fields = ('id', 'address', 'services', 'description', 'name')


