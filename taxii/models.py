from django.db import models
from django.contrib.auth.models import User
from dateutil.tz import tzutc
import datetime

MAX_ID_LEN      = 128
MAX_TITLE_LEN   = 128

class ProtocolBindingId(models.Model):
    """
    Represents a protocol binding id, used to establish the exchange protocol
    supported by a TAXII implementation.

    Ex:
    HTTP protocol binding id : "urn:taxii.mitre.org:protocol:http:1.0"
    HTTPS protocol binding id : "urn:taxii.mitre.org:protocol:https:1.0"
    """
    title = models.CharField(max_length=MAX_TITLE_LEN, blank=True)
    description = models.TextField(blank=True)
    binding_id = models.CharField(max_length=MAX_ID_LEN)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        if self.title:
            return u'%s' % (self.title)
        else:
            return u'%s' % (self.binding_id)

    class Meta:
        verbose_name = "Protocol Binding Id"

class ContentBindingId(models.Model):
    """
    Represents a content binding id, used to establish the supported content
    types for a given TAXII exchange (e.g., Poll, Inbox, etc.).

    Ex:
    STIX v1.0 content binding id : "urn:stix.mitre.org:xml:1.0"
    """
    title = models.CharField(max_length=MAX_TITLE_LEN, blank=True)
    description = models.TextField(blank=True)
    binding_id = models.CharField(max_length=MAX_ID_LEN)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        if self.title:
            return u'%s' % (self.title)
        else:
            return u'%s' % (self.binding_id)

    class Meta:
        verbose_name = "Content Binding Id"

class MessageBindingId(models.Model):
    """
    Represents a message binding id, used to establish the supported syntax
    for a given TAXII exchange, "e.g., XML".

    Ex:
    XML message binding id : "urn:taxii.mitre.org:message:xml:1.0"
    """
    title = models.CharField(max_length=MAX_TITLE_LEN, blank=True)
    description = models.TextField(blank=True)
    binding_id = models.CharField(max_length=MAX_ID_LEN)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        if self.title:
            return u'%s' % (self.title)
        else:
            return u'%s' % (self.binding_id)

    class Meta:
        verbose_name = "Message Binding Id"

class DataFeedPushMethod(models.Model):
    """
    Used to establish the protocols that can be used to push content via
    a subscription. This appears in a Feed Information Response message,
    as defined by the TAXII Services Specification.
    """
    title = models.CharField(max_length=MAX_TITLE_LEN, blank=True)
    description = models.TextField(blank=True)
    protocol_binding = models.ForeignKey(ProtocolBindingId)
    message_binding = models.ForeignKey(MessageBindingId)

    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        if self.title:
            return u'%s' % (self.title)
        else:
            return u'%s | %s' % (self.protocol_binding, self.message_binding)

    class Meta:
        verbose_name = "Data Feed Push Method"

class DataFeedPollInformation(models.Model):
    """
    Used to establish the supported protocols and address of a Data Feed.
    This appears in a Feed Information Response message, as defined by the
    TAXII Services Specification.
    """
    title = models.CharField(max_length=MAX_TITLE_LEN, blank=True)
    description = models.TextField(blank=True)
    address = models.URLField()
    protocol_binding = models.ForeignKey(ProtocolBindingId)
    message_bindings = models.ManyToManyField(MessageBindingId)

    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        if self.title:
            return u'%s' % (self.title)
        else:
            return u'%s | %s' % (self.protocol_binding, self.message_binding)

    class Meta:
        ordering = ['address']
        verbose_name = "Data Feed Poll Information"
        verbose_name_plural = "Data Feed Poll Information"

class DataFeedSubscriptionMethod(models.Model):
    """
    Used to identify the protocol and address of the TAXII daemon hosting
    the Feed Management Service that can process subscriptions for a TAXII
    Data Feed. This appears in a Feed Information Response message, as defined
    by the TAXII Services Specification.
    """
    title = models.CharField(max_length=MAX_TITLE_LEN, blank=True)
    description = models.TextField(blank=True)
    address = models.URLField()
    protocol_binding = models.ForeignKey(ProtocolBindingId)
    message_bindings = models.ManyToManyField(MessageBindingId)

    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        if self.title:
            return '%s %s' % (self.id, self.title)
        else:
            return u'%s | %s' % (self.protocol_binding, self.message_binding)

    class Meta:
        ordering = ['address']
        verbose_name = "Data Feed Subscription Method"

class ContentBlock(models.Model):
    """Represents the content block of a TAXII Poll Response or Inbox message."""
    title = models.CharField(max_length=MAX_TITLE_LEN, blank=True) # not required by TAXII
    description = models.TextField(blank=True) # not required by TAXII

    timestamp_label = models.DateTimeField(default=lambda:datetime.datetime.now(tzutc())) # need to ensure uniqueness of this field
    submitted_by = models.ForeignKey(User, blank=True, null=True) # Not sure this is needed, but we track it anyway
    message_id = models.CharField(max_length=MAX_ID_LEN, blank=True) # associated message id if present. is there always a 1-to-1 for message ids and content blocks

    #TAXII Properties of a content block
    content_binding = models.ForeignKey(ContentBindingId)
    content = models.TextField()
    padding = models.TextField(blank=True)

    date_created = models.DateTimeField(auto_now_add=True) # look at this for problems with apache instances
    date_updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return u'%s' % (self.id)

    class Meta:
        ordering = ['timestamp_label']
        verbose_name = "Content Block"

class DataFeed(models.Model):
    """Represents a TAXII Data Feed"""
    name = models.CharField(max_length=MAX_TITLE_LEN) # this will be used to access this data feed
    description = models.TextField(blank=True)
    users = models.ManyToManyField(User, blank=True, null=True) # users allowed to access this data feed.
    #authentication_required = models.BooleanField(default=True)
    supported_content_bindings = models.ManyToManyField(ContentBindingId)
    push_methods = models.ManyToManyField(DataFeedPushMethod)
    poll_service_instances = models.ManyToubscription_methodsanyField(DataFeedPollInformation)
    subscription_methods = models.ManyToManyField(DataFeedSubscriptionMethod, blank=True, null=True)
    content_blocks = models.ManyToManyField(ContentBlock, blank=True, null=True)

    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return u'%s' % (self.name)

    class Meta:
        ordering = ['name']
        verbose_name = "Data Feed"

class DataFeedSubscription(models.Model):
    """Represents a Data Feed Subscription. This is not used by TAXII at the moment."""
    subscription_id = models.CharField(max_length=MAX_ID_LEN, unique=True) # uri formatted subscription id
    user = models.ForeignKey(User)
    data_feed = models.ForeignKey(DataFeed)
    data_feed_method = models.ForeignKey(DataFeedSubscriptionMethod)
    active = models.BooleanField(default=True)
    expires = models.DateTimeField()

    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return u'%s' % (self.title)

    class Meta:
        ordering = ['subscription_id']
        verbose_name = "Data Feed Subscription"

class Inbox(models.Model):
    """
    Characterizes a TAXII Inbox. Inboxes are the mechanism by which TAXII consumers
    receive data from TAXII publishers. This Inbox implementation allows an Inbox
    to be "bound" to zero or more Data Feeds, meaning that data received by an Inbox
    can populate Data Feeds if a user configures it as such.
    """
    name = models.CharField(max_length=MAX_TITLE_LEN, unique=True) # this will become part of the URL where it can be accessed at
    description = models.TextField(blank=True)
    supported_content_bindings = models.ManyToManyField(ContentBindingId)
    supported_message_bindings = models.ManyToManyField(MessageBindingId)
    content_blocks = models.ManyToManyField(ContentBlock, blank=True, null=True) # content blocks associated with this inbox
    supported_protocol_binding = models.ForeignKey(ProtocolBindingId)
    data_feeds = models.ManyToManyField(DataFeed, blank=True, null=True) # data received at an inbox will automatically be made available on these data feeds
    users = models.ManyToManyField(User, blank=True, null=True) # users allowed to access this inbox

    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        ordering = ['name']
        verbose_name = "Inbox"
        verbose_name_plural = "Inboxes"

class ContentBlockRTIR(models.Model):
    """Represents the nexus between the RTIR ticket and the content block."""
    rtir_id = models.IntegerField(unique=True)
    content_block = models.ForeignKey(ContentBlock)

class RemoteDataFeedPollInformation(models.Model):
    title = models.CharField(max_length=MAX_TITLE_LEN, blank=True)
    description = models.TextField(blank=True)
    address = models.URLField()
    protocol_binding = models.ForeignKey(ProtocolBindingId)
    message_bindings = models.ManyToManyField(MessageBindingId)

    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        if self.title:
            return u'%s' % (self.title)
        else:
            return u'%s | %s' % (self.protocol_binding, self.message_binding)

    class Meta:
        ordering = ['address']
        verbose_name = "Remote Data Feed Poll Information"
        verbose_name_plural = "Remote Data Feed Poll Information"


class RemoteDataFeed(models.Model):
    name = models.CharField(max_length=MAX_TITLE_LEN) # this will be used to access this data feed
    description = models.TextField(blank=True)
    supported_content_bindings = models.ManyToManyField(ContentBindingId)
    push_methods = models.ManyToManyField(DataFeedPushMethod)
    poll_service_instance = models.ForeignKey(RemoteDataFeedPollInformation, null=True)
    subscription_methods = models.ManyToManyField(DataFeedSubscriptionMethod, blank=True, null=True)
    content_blocks = models.ManyToManyField(ContentBlock, blank=True, null=True)

    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return u'%s' % (self.name)

    class Meta:
        ordering = ['name']
        verbose_name = "Remote Data Feed"

class RemoteInbox(models.Model):
    name = models.CharField(max_length=MAX_TITLE_LEN, unique=True) # this will become part of the URL where it can be accessed at
    description = models.TextField(blank=True)
    supported_content_bindings = models.ManyToManyField(ContentBindingId)
    supported_message_bindings = models.ManyToManyField(MessageBindingId)
    supported_protocol_binding = models.ForeignKey(ProtocolBindingId)
    data_feed = models.ForeignKey(DataFeed, blank=True) # data received at an inbox will automatically be made available on these data feeds
    address = models.URLField()
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        ordering = ['name']
        verbose_name = "Remote Inbox"
        verbose_name_plural = "Remote Inboxes"


