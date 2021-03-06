from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from flask import _request_ctx_stack

class BadHeaderError(Exception): pass


class Attachment(object):

    """
    Encapsulates file attachment information.

    :versionadded: 0.3.5

    :param filename: filename of attachment
    :param content_type: file mimetype
    :param data: the raw file data
    :param disposition: content-disposition (if any)
 
    """

    def __init__(self, filename=None, content_type=None, data=None,
        disposition=None): 

        self.filename = filename
        self.content_type = content_type
        self.data = data
        self.disposition = disposition or 'attachment'


class Message(object):
    
    """
    Encapsulates an email message.

    :param subject: email subject header
    :param recipients: list of email addresses
    :param body: plain text message
    :param html: HTML message
    :param sender: email sender address, or **DEFAULT_MAIL_SENDER** by default
    :param cc: CC list
    :param bcc: BCC list
    :param attachments: list of Attachment instances
    """

    def __init__(self, subject, 
                 recipients=None, 
                 body=None, 
                 html=None, 
                 sender=None,
                 cc=None,
                 bcc=None,
                 attachments=None):


        if sender is None:
            app = _request_ctx_stack.top.app
            sender = app.config.get("DEFAULT_MAIL_SENDER")

        if isinstance(sender, tuple):
            # sender can be tuple of (name, address)
            sender = "%s <%s>" % sender

        self.subject = subject
        self.sender = sender
        self.body = body
        self.html = html

        self.cc = cc
        self.bcc = bcc 

        if recipients is None:
            recipients = []

        self.recipients = list(recipients)
        
        if attachments is None:
            attachments = []

        self.attachments = attachments

    @property
    def send_to(self):
        return set(self.recipients) | set(self.bcc or ()) | set(self.cc or ())

    def get_message(self):
        """Craft email message
        """

        msg = MIMEMultipart()
        msg["From"] = self.sender
        msg["To"] = ','.join(self.recipients)
        msg["Subject"] = self.subject
        msg.attach(MIMEText(self.body, 'plain'))
        msg.attach(MIMEText(self.html, 'html'))
        return msg.as_string()

        #response = MailResponse(Subject=self.subject, 
        #                        To=self.recipients,
        #                        From=self.sender,
        #                        Body=self.body,
        #                        Html=self.html)
        # 
        #if self.bcc:
        #    response.base['Bcc'] = self.bcc
        # 
        #if self.cc:
        #    response.base['Cc'] = self.cc
        # 
        #for attachment in self.attachments:
        # 
        #    response.attach(attachment.filename, 
        #                    attachment.content_type, 
        #                    attachment.data, 
        #                    attachment.disposition)
        #
        #return response
    
    def is_bad_headers(self):
        """
        Checks for bad headers i.e. newlines in subject, sender or recipients.
        """
       
        for val in [self.subject, self.sender] + self.recipients:
            for c in '\r\n':
                if c in val:
                    return True
        return False
        
    def send(self, connection):
        """
        Verifies and sends the message.
        """
        
        assert self.recipients, "No recipients have been added"
        assert self.body or self.html, "No body or HTML has been set"
        assert self.sender, "No sender address has been set"

        if self.is_bad_headers():
            raise BadHeaderError

        connection.send(self)

    def add_recipient(self, recipient):
        """
        Adds another recipient to the message.
        
        :param recipient: email address of recipient.
        """
        
        self.recipients.append(recipient)

    def attach(self, 
               filename=None, 
               content_type=None, 
               data=None,
               disposition=None):
        
        """
        Adds an attachment to the message.
        
        :param filename: filename of attachment
        :param content_type: file mimetype
        :param data: the raw file data
        :param disposition: content-disposition (if any)
        """

        self.attachments.append(
            Attachment(filename, content_type, data, disposition))

